import logging
import logging.config
from pathlib import Path
import sys
import time

import PyQt6.QtCore as qtc
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
import PyQt6.QtWidgets as qtw

from annotation_tool.annotation.timeline import QTimeLine
from annotation_tool.media_reader import meta_data
import annotation_tool.network.controller as network
from annotation_tool.settings import settings

from . import __version__
from .annotation.controller import AnnotationController
from .data_model.annotation import Annotation
from .gui import GUI, LayoutPosition
from .media.media import QMediaWidget  # This raises all the debug-messages on startup
from .mediator import Mediator
from .playback import QPlaybackWidget
from .utility import filehandler


class MainApplication(qtw.QApplication):
    update_media_pos = qtc.pyqtSignal(int)
    update_annotation_pos = qtc.pyqtSignal(int)
    load_media = qtc.pyqtSignal(Path, list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Control-Attributes
        self.current_annotation = None
        self.n_frames = 0
        self.mediator = Mediator()

        # timer for automatic saving
        self.save_timer = qtc.QTimer()
        self.save_timer.timeout.connect(self.autosave)
        self.save_interval = 120  # 2 minutes
        self.last_save = time.time()
        self.save_timer.start(30 * 1000)  # check every 30 seconds

        # Widgets
        self.gui = GUI()
        self.annotation_controller = AnnotationController()
        self.playback = QPlaybackWidget()
        self.media_player = QMediaWidget()
        self.timeline = QTimeLine()

        self.gui.set_widget(self.playback, LayoutPosition.TOP_LEFT)
        self.gui.set_widget(self.media_player, LayoutPosition.MIDDLE)
        self.gui.set_widget(self.timeline, LayoutPosition.BOTTOM_MIDDLE)

        # CONNECTIONS
        # from QPlaybackWidget
        self.playback.playing.connect(self.media_player.play)
        self.playback.paused.connect(self.media_player.pause)
        self.playback.replay_speed_changed.connect(self.media_player.set_replay_speed)

        # from media_player
        self.media_player.additional_media_changed.connect(
            self.set_additional_media_paths
        )
        self.load_media.connect(self.media_player.load)
        self.media_player.loaded.connect(self.media_player_loaded)

        # from QAnnotationWidget
        self.annotation_controller.samples_changed.connect(self.timeline.set_samples)
        self.annotation_controller.right_widget_changed.connect(
            lambda w: self.gui.set_widget(w, LayoutPosition.RIGHT)
        )
        self.annotation_controller.tool_widget_changed.connect(
            lambda w: self.gui.set_widget(w, LayoutPosition.BOTTOM_LEFT)
        )
        self.annotation_controller.start_loop.connect(self.mediator.start_loop)
        self.annotation_controller.stop_loop.connect(self.mediator.stop_loop)
        self.annotation_controller.pause_replay.connect(self.playback.pause)
        # TODO refactoring
        self.gui.set_widget(
            self.annotation_controller.controller.main_widget, LayoutPosition.RIGHT
        )
        self.gui.set_widget(
            self.annotation_controller.controller.tool_widget,
            LayoutPosition.BOTTOM_LEFT,
        )

        # from GUI
        self.gui.user_action.connect(self.playback.on_user_action)
        self.gui.user_action.connect(self.annotation_controller.on_user_action)
        self.gui.save_pressed.connect(self.save_annotation)
        self.gui.load_annotation.connect(self.load_state)
        self.gui.settings_changed.connect(self.settings_changed)
        self.gui.exit_pressed.connect(self.shutdown)
        self.gui.annotation_mode_changed.connect(self.annotation_controller.change_mode)

        # Init mediator
        self.mediator.add_receiver(self.timeline)
        self.mediator.add_receiver(self.annotation_controller)
        self.mediator.add_receiver(self.media_player)
        self.mediator.add_receiver(self.playback)
        self.mediator.add_emitter(self.timeline)
        self.mediator.add_emitter(self.annotation_controller)
        self.mediator.add_emitter(self.media_player)
        self.mediator.add_emitter(self.playback)

    @qtc.pyqtSlot(Annotation)
    def load_state(self, annotation: Annotation):
        """
        Core function to update the application state.
        """
        if annotation is not None:
            self.current_annotation = annotation

            meta_data_dict = meta_data(annotation.path)
            n_frames = meta_data_dict["n_frames"]
            fps = meta_data_dict["fps"]

            # load media
            self.load_media.emit(
                annotation.path, annotation.get_additional_media_paths()
            )

            # update network module
            network.update_state(
                file=annotation.path, num_labels=len(annotation.dataset.scheme)
            )

            # save for later reuse
            self.n_frames = n_frames

            # reset playback
            self.playback.reset()

            # update mediator
            self.mediator.n_frames = n_frames

            # update playback
            self.playback.n_frames = n_frames

            # adjust timeline
            self.timeline.set_range(n_frames, fps)

            # update annotation controller
            self.annotation_controller.load(
                annotation.samples,
                annotation.dataset.scheme,
                annotation.dataset.dependencies,
                n_frames,
            )

            self.mediator.reset_position()

            self.save_annotation()

        else:
            raise RuntimeError("State must not be None")

    @qtc.pyqtSlot(list)
    def set_additional_media_paths(self, paths: list):
        if self.current_annotation is not None:
            self.current_annotation.set_additional_media_paths(paths)
        else:
            raise RuntimeError("No current annotation set")

    @qtc.pyqtSlot()
    def media_player_loaded(self):
        if self.current_annotation is not None:
            self.media_player.additional_media_changed.connect(
                self.set_additional_media_paths
            )
        else:
            raise RuntimeError("No current annotation set")

    def save_annotation(self):
        if self.current_annotation is not None:
            samples = self.annotation_controller.controller.samples

            if len(samples) > 0:
                assert samples[-1].end_position + 1 == self.n_frames
            else:
                assert self.n_frames == 0
            self.current_annotation.samples = (
                samples  # this also writes the update to disk
            )

            # write to statusbar
            annotation_name = self.current_annotation.name
            self.gui.write_to_statusbar(f"Saved annotation {annotation_name}")

        self.last_save = time.time()

    @qtc.pyqtSlot()
    def autosave(self):
        if time.time() - self.last_save > self.save_interval:
            self.save_annotation()

    @qtc.pyqtSlot()
    def settings_changed(self):
        filehandler.set_logging_level(settings.logging_level)

    def update_theme(self):
        self.setStyle("Fusion")

        if settings.color_theme == "dark":
            # # Now use a palette to switch to dark colors:
            dark_palette = QPalette(self.style().standardPalette())
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(
                QPalette.ColorRole.HighlightedText, QColor(35, 35, 35)
            )
            dark_palette.setColor(
                QPalette.ColorGroup.Active,
                QPalette.ColorRole.Button,
                QColor(53, 53, 53),
            )
            dark_palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.ButtonText,
                Qt.GlobalColor.darkGray,
            )
            dark_palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.WindowText,
                Qt.GlobalColor.darkGray,
            )
            dark_palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.Text,
                Qt.GlobalColor.darkGray,
            )
            dark_palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.Light,
                QColor(53, 53, 53),
            )
            self.setPalette(dark_palette)
        elif settings.color_theme == "light":
            light_palette = QPalette(self.style().standardPalette())
            light_palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
            light_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
            light_palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
            light_palette.setColor(
                QPalette.ColorRole.AlternateBase, Qt.GlobalColor.white
            )
            light_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            light_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
            light_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
            light_palette.setColor(QPalette.ColorRole.Button, Qt.GlobalColor.white)
            light_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
            light_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            light_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            light_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            light_palette.setColor(
                QPalette.ColorRole.HighlightedText, QColor(35, 35, 35)
            )
            light_palette.setColor(
                QPalette.ColorGroup.Active,
                QPalette.ColorRole.Button,
                Qt.GlobalColor.white,
            )
            light_palette.setColor(
                QPalette.ColorGroup.Disabled,
                QPalette.ColorRole.ButtonText,
                Qt.GlobalColor.darkGray,
            )

            self.setPalette(light_palette)

        elif settings.color_theme == "system":
            # This is disabled for now, since icons might not be visible
            raise NotImplementedError(
                "System theme is not implemented yet, please use light or dark theme"
            )
            # self.setPalette(QPalette())
            # get background color from system
            # background_color = self.palette().color(QPalette.ColorRole.Window)

        else:
            raise ValueError(f"Unknown color theme {settings.color_theme}")

        font = self.font()
        font.setPointSize(settings.font_size)
        self.setFont(font)

        # hack for updating color of histogram in retrieval-widget
        from annotation_tool.annotation.retrieval.controller import RetrievalAnnotation

        if self.annotation_controller is not None and isinstance(
            self.annotation_controller.controller, RetrievalAnnotation
        ):
            self.annotation_controller.controller.main_widget.histogram.plot_data()

    def closeEvent(self, event):
        self.shutdown()
        event.accept()

    @qtc.pyqtSlot()
    def shutdown(self):
        """
        This method is called when the application is closed.
        It saves the current annotation and closes the main window.
        """
        self.save_timer.stop()
        self.save_annotation()
        self.media_player.shutdown()
        self.gui.close()  # close main window
        logging.info("Successfully stopped application!")


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def main():
    lvl = settings.logging_level
    filehandler.set_logging_level(lvl)

    sys.excepthook = except_hook
    app = MainApplication(sys.argv)

    # set font for app
    font = app.font()
    font.setPointSize(settings.font_size)
    app.setFont(font)

    app.setStyle("Fusion")

    app.update_theme()

    logging.info(f"PyQt-Version: {qtc.PYQT_VERSION_STR}")
    logging.info(f"Python-Version: {sys.version}")
    logging.info(f"Platform: {sys.platform}")
    logging.info(f"Version: {__version__}")
    logging.info("Starting application...")

    sys.exit(app.exec())
