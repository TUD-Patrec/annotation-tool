import logging
import logging.config
import sys

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.annotation.modes import AnnotationMode
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

main_application = None


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
        self.gui.save_pressed.connect(self.save_annotation)
        self.gui.load_annotation.connect(self.load_state)
        self.gui.annotate_pressed.connect(self.annotation_controller.annotate)
        self.gui.merge_left_pressed.connect(
            lambda: self.annotation_controller.merge(True)
        )
        self.gui.merge_right_pressed.connect(
            lambda: self.annotation_controller.merge(False)
        )
        self.gui.cut_pressed.connect(self.annotation_controller.cut)
        self.gui.cut_and_annotate_pressed.connect(
            self.annotation_controller.cut_and_annotate
        )
        self.gui.play_pause_pressed.connect(self.playback.play_stop_button.trigger)
        self.gui.skip_frames.connect(lambda x, y: self.playback.skip_frames.emit(x, y))
        self.gui.decrease_speed_pressed.connect(self.playback.decrease_speed)
        self.gui.increase_speed_pressed.connect(self.playback.increase_speed)
        self.gui.undo_pressed.connect(self.annotation_controller.undo)
        self.gui.redo_pressed.connect(self.annotation_controller.redo)
        self.gui.accept_pressed.connect(self.annotation_controller.accept)
        self.gui.reject_pressed.connect(self.annotation_controller.reject)
        self.gui.modify_pressed.connect(self.annotation_controller.modify)
        self.gui.change_filter_pressed.connect(self.annotation_controller.select_filter)
        self.gui.settings_changed.connect(self.settings_changed)
        self.gui.settings_changed.connect(self.media_player.settings_changed)
        self.gui.exit_pressed.connect(self.media_player.shutdown)
        self.gui.use_manual_annotation.connect(
            lambda: self.annotation_controller.change_mode(AnnotationMode.MANUAL)
        )
        self.gui.use_retrieval_mode.connect(
            lambda: self.annotation_controller.change_mode(AnnotationMode.RETRIEVAL)
        )

        # Init mediator
        self.mediator.add_receiver(self.timeline)
        self.mediator.add_receiver(self.annotation_controller)
        self.mediator.add_receiver(self.media_player)
        self.mediator.add_receiver(self.playback)
        self.mediator.add_emitter(self.timeline)
        self.mediator.add_emitter(self.media_player)
        self.mediator.add_emitter(self.playback)

        # ui
        self.update_theme()
        self.update_font()

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
        return
        darkmode = settings.darkmode
        file = (
            qtc.QFile(":/dark/stylesheet.qss")
            if darkmode
            else qtc.QFile(":/light/stylesheet.qss")
        )
        file.open(qtc.QFile.ReadOnly | qtc.QFile.Text)
        stream = qtc.QTextStream(file)
        self.setStyleSheet(stream.readAll())

        # hack for updating color of histogram in retrieval-widget
        from src.annotation.retrieval.controller import RetrievalAnnotation

        if self.annotation_controller is not None and isinstance(
            self.annotation_controller.controller, RetrievalAnnotation
        ):
            self.annotation_controller.controller.main_widget.histogram.plot()

    def update_font(self):
        print(self.styleSheet())
        font = self.font()
        font.setPointSize(settings.font_size)
        self.setFont(font)

    def closeEvent(self, event):
        self.save_annotation()
        self.media_player.shutdown()
        event.accept()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def make_app() -> qtg.QApplication:
    from . import __version__

    app = MainApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Annotation Tool")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("TU Dortmund")
    app.setOrganizationDomain("tu-dortmund.de")
    app.setWindowIcon(qtg.QIcon(":/icons/icon.png"))
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationDisplayName("Annotation Tool")
    return app


def get_app() -> qtg.QApplication:
    if qtc.QCoreApplication.instance():
        return qtc.QCoreApplication.instance()
    else:
        return make_app()


def main():
    # set font
    font = qtg.QFont()
    font.setPointSize(settings.font_size)
    qtg.QApplication.setFont(font)

    sys.excepthook = except_hook
    app = make_app()
    sys.exit(app.exec_())
