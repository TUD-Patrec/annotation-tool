import logging
import logging.config
import sys
import time

import PyQt6.QtCore as qtc
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
import PyQt6.QtWidgets as qtw

from annotation_tool.annotation.timeline import QTimeLine
from annotation_tool.media_reader import media_reader, set_fallback_fps
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
from .utility.functions import FrameTimeMapper

# init media_reader
set_fallback_fps(settings.refresh_rate)


class MainApplication(qtw.QApplication):
    update_media_pos = qtc.pyqtSignal(int)
    update_annotation_pos = qtc.pyqtSignal(int)
    load_media = qtc.pyqtSignal(str, list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Controll-Attributes
        self.current_annotation = None
        self.n_frames = 0
        self.mediator = Mediator()

        # timer for automatic saving
        self.save_timer = qtc.QTimer()
        self.save_timer.timeout.connect(self.autosave)
        self.save_interval = 5  # 1 minute
        self.last_save = time.time()
        self.save_timer.start(30 * 1000)  # check every 10 seconds

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
        self.gui.settings_changed.connect(self.media_player.settings_changed)
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
        if annotation is not None:
            # store annotation
            self.current_annotation = annotation

            media = media_reader(path=annotation.path)
            duration = media.duration
            n_frames = len(media)

            FrameTimeMapper.instance().update(n_frames=n_frames, millis=duration)

            # load media
            # self.media_player.additional_media_changed.disconnect()  # disconnect to filter out outdated signals
            # self.media_player.load(media.path)
            self.load_media.emit(
                annotation.path, annotation.get_additional_media_paths()
            )  # noqa TODO: Make get_additional_media_paths() a property

            # update network module
            network.update_file(media.path)

            # save for later reuse
            self.n_frames = n_frames

            # reset playback
            self.playback.reset()

            # update mediator
            self.mediator.n_frames = n_frames

            # update playback
            self.playback.n_frames = n_frames

            # adjust timeline
            self.timeline.set_range(n_frames)

            # update annotation controller
            self.annotation_controller.load(
                annotation.samples,
                annotation.dataset.scheme,
                annotation.dataset.dependencies,
                n_frames,
            )

            # self.mediator.set_position(0, force_update=True)
            self.mediator.reset_position()

            self.save_annotation()

        else:
            raise RuntimeError("State must not be None")

    @qtc.pyqtSlot(list)
    def set_additional_media_paths(self, paths: list):
        assert self.current_annotation is not None
        self.current_annotation.set_additional_media_paths(paths)

    @qtc.pyqtSlot()
    def media_player_loaded(self):
        assert self.current_annotation is not None
        self.media_player.additional_media_changed.connect(
            self.set_additional_media_paths
        )  # reconnect after loading

        # additional_media = self.current_annotation.get_additional_media_paths()
        # self.media_player.set_additional_media(additional_media)
        logging.debug("media_player_loaded")

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

        set_fallback_fps(settings.refresh_rate)

        if self.current_annotation is not None:
            media = media_reader(path=self.current_annotation.path)
            duration = media.duration
            n_frames = len(media)

            FrameTimeMapper.instance().update(n_frames=n_frames, millis=duration)

        self.timeline.update()

    def update_theme(self):
        self.setStyle("Fusion")

        if settings.darkmode:
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
        else:
            self.setPalette(QPalette())
            # self.setPalette(self.style().standardPalette())  # reset to system default

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
        logging.info("Closing application via closeEvent")
        self.shutdown()
        event.accept()

    @qtc.pyqtSlot()
    def shutdown(self):
        """
        This method is called when the application is closed.
        It saves the current annotation and closes the main window.
        """
        logging.info("Closing application")
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

    # styles: 'Breeze', 'Oxygen', 'QtCurve', 'Windows', 'Fusion'
    app.setStyle("Fusion")

    app.update_theme()

    logging.info(f"PyQt-Version: {qtc.PYQT_VERSION_STR}")
    logging.info(f"Python-Version: {sys.version}")
    logging.info(f"Platform: {sys.platform}")
    logging.info(f"Version: {__version__}")
    logging.info("Starting application...")

    sys.exit(app.exec())
