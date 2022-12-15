import logging
import logging.config
import sys

import PyQt5.QtCore as qtc
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
import PyQt5.QtWidgets as qtw
import qdarkstyle

from src.annotation.timeline import QTimeLine
import src.network.controller as network
from src.settings import settings
import src.utility.breeze_resources  # noqa: F401

from .annotation.controller import AnnotationController
from .data_model.globalstate import GlobalState
from .gui import GUI, LayoutPosition
from .media.media import QMediaWidget
from .mediator import Mediator
from .playback import QPlaybackWidget
from .utility import filehandler
from .utility.functions import FrameTimeMapper


class MainApplication(qtw.QApplication):
    update_media_pos = qtc.pyqtSignal(int)
    update_annotation_pos = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Controll-Attributes
        self.global_state = None
        self.n_frames = 0
        self.mediator = Mediator()

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
        self.media_player.cleanedUp.connect(self.gui.cleaned_up)

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
        self.gui.exit_pressed.connect(self.media_player.shutdown)
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

    @qtc.pyqtSlot(GlobalState)
    def load_state(self, state: GlobalState):
        if state is not None:
            duration = state.media.duration
            n_frames = state.media.n_frames

            FrameTimeMapper.instance().update(n_frames=n_frames, millis=duration)

            # load media
            self.media_player.load(state.media.path)

            # update network module
            network.update_file(state.media.path)

            # save for later reuse
            self.n_frames = n_frames

            # reset playback
            self.playback.reset()

            # store annotation
            self.global_state = state

            # update mediator
            self.mediator.n_frames = n_frames

            # update playback
            self.playback.n_frames = n_frames

            # adjust timeline
            self.timeline.set_range(n_frames)

            # update annotation controller
            self.annotation_controller.load(
                state.samples,
                state.dataset.scheme,
                state.dataset.dependencies,
                n_frames,
            )

            self.mediator.set_position(0, force_update=True)

            self.save_annotation()

        else:
            raise RuntimeError("State must not be None")

    def save_annotation(self):
        if self.global_state is None:
            logging.info("Nothing to save - annotation-object is None")
        else:
            logging.info("Saving current state")
            samples = self.annotation_controller.controller.samples

            if len(samples) > 0:
                assert samples[-1].end_position + 1 == self.n_frames
            else:
                assert self.n_frames == 0
            self.global_state.samples = samples  # this also writes the update to disk

    @qtc.pyqtSlot()
    def settings_changed(self):
        log_config_dict = filehandler.logging_config()
        log_config_dict["handlers"]["screen_handler"]["level"] = (
            "DEBUG" if settings.debugging_mode else "WARNING"
        )
        logging.config.dictConfig(log_config_dict)

        if self.global_state is not None:
            FrameTimeMapper.instance().update(
                n_frames=self.global_state.media.n_frames,
                millis=self.global_state.media.duration,
            )

        self.timeline.update()

    def update_theme(self):
        self.setStyle("Fusion")

        if settings.darkmode:
            # # Now use a palette to switch to dark colors:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)
            dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, Qt.darkGray)
            dark_palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
            dark_palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53))
            self.setPalette(dark_palette)
        else:
            self.setPalette(self.style().standardPalette())

        font = self.font()
        font.setPointSize(settings.font_size)
        self.setFont(font)

        return
        # TODO fix
        if settings.darkmode is None:
            # TODO this will never be true -> for testing
            if settings.darkmode:
                self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            else:
                from qdarkstyle.light.palette import LightPalette

                self.setStyleSheet(
                    qdarkstyle._load_stylesheet(qt_api="pyqt5", palette=LightPalette)
                )

        # TODO fix
        if settings.darkmode is None:
            # hack for updating color of histogram in retrieval-widget
            from src.annotation.retrieval.controller import RetrievalAnnotation

            if self.annotation_controller is not None and isinstance(
                self.annotation_controller.controller, RetrievalAnnotation
            ):
                self.annotation_controller.controller.main_widget.histogram.plot_data()

    def closeEvent(self, event):
        self.save_annotation()
        self.media_player.shutdown()
        event.accept()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def main():
    sys.excepthook = except_hook
    app = MainApplication(sys.argv)

    # set font for app
    font = app.font()
    font.setPointSize(settings.font_size)
    app.setFont(font)

    # styles: 'Breeze', 'Oxygen', 'QtCurve', 'Windows', 'Fusion'
    app.setStyle("Fusion")

    app.update_theme()
    sys.exit(app.exec_())
