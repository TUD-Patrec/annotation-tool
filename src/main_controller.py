import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import sys, logging, logging.config

from .data_classes.globalstate import GlobalState
from src.annotation.annotation_widget import QAnnotationWidget
from .gui import GUI
from .mediator import Mediator
from .playback import QPlaybackWidget
from .display_current_sample import QDisplaySample
from src.retrieval_backend.controller import QRetrievalWidget
from src.data_classes.settings import Settings
from src.annotation.timeline import QTimeLine
from .utility.functions import FrameTimeMapper
from .utility import filehandler

from src.utility.breeze_resources import *

from .media import QMediaWidget


class MainApplication(qtw.QApplication):
    update_media_pos = qtc.pyqtSignal(int)
    update_annotation_pos = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Controll-Attributes
        self.global_state = None
        self.mediator = Mediator()

        # Widgets
        self.gui = GUI()
        self.annotation_widget = QAnnotationWidget()
        self.playback = QPlaybackWidget()
        self.media_player = QMediaWidget()
        self.timeline = QTimeLine()
        self.flex_widget = None

        self.gui.set_left_widget(self.playback)
        self.gui.set_central_widget(self.media_player)
        bottom_widget = qtw.QWidget()
        bottom_widget.setLayout(qtw.QHBoxLayout())
        bottom_widget.layout().addWidget(self.annotation_widget)
        bottom_widget.layout().addWidget(self.timeline, stretch=1)
        self.gui.set_bottom_widget(bottom_widget)

        # CONNECTIONS
        # from QPlaybackWidget
        self.playback.playing.connect(self.media_player.play)
        self.playback.paused.connect(self.media_player.pause)
        self.playback.replay_speed_changed.connect(self.media_player.set_replay_speed)

        # from media_player
        self.media_player.cleanedUp.connect(self.gui.cleaned_up)

        # from QAnnotationWidget
        self.annotation_widget.samples_changed.connect(self.timeline.set_samples)

        # from GUI
        self.gui.save_pressed.connect(self.save_annotation)
        self.gui.load_annotation.connect(self.load_state)
        self.gui.annotate_pressed.connect(self.annotation_widget.annotate_btn.click)
        self.gui.merge_left_pressed.connect(self.annotation_widget.merge_left_btn.click)
        self.gui.merge_right_pressed.connect(
            self.annotation_widget.merge_right_btn.click
        )
        self.gui.cut_pressed.connect(self.annotation_widget.cut_btn.click)
        self.gui.cut_and_annotate_pressed.connect(
            self.annotation_widget.cut_and_annotate_btn.click
        )
        self.gui.play_pause_pressed.connect(self.playback.play_stop_button.trigger)
        self.gui.skip_frames.connect(lambda x, y: self.playback.skip_frames.emit(x, y))
        self.gui.decrease_speed_pressed.connect(self.playback.decrease_speed)
        self.gui.increase_speed_pressed.connect(self.playback.increase_speed)
        self.gui.undo_pressed.connect(self.annotation_widget.undo)
        self.gui.redo_pressed.connect(self.annotation_widget.redo)
        self.gui.settings_changed.connect(self.settings_changed)
        self.gui.settings_changed.connect(self.media_player.settings_changed)
        self.gui.exit_pressed.connect(self.media_player.shutdown)
        self.gui.use_manual_annotation.connect(self.load_manual_annotation)
        self.gui.use_retrieval_mode.connect(self.load_retrieval_mode)

        self.load_manual_annotation()

        # Init mediator
        self.mediator.add_receiver(self.timeline)
        self.mediator.add_receiver(self.annotation_widget)
        self.mediator.add_receiver(self.media_player)
        self.mediator.add_receiver(self.playback)
        self.mediator.add_emitter(self.timeline)
        self.mediator.add_emitter(self.media_player)
        self.mediator.add_emitter(self.playback)

    @qtc.pyqtSlot(GlobalState)
    def load_state(self, state):
        FrameTimeMapper.instance().load_state(state.frames, state.duration)

        # reset playback
        self.playback.reset()

        # store annotation
        self.global_state = state

        # update mediator
        self.mediator.n_frames = state.n_frames

        # update playback
        self.playback.n_frames = state.n_frames

        # load annotation in widgets
        self.timeline.set_range(state.n_frames)
        self.annotation_widget.load_state(state)
        self.media_player.load_state(state)

        if isinstance(self.flex_widget, QRetrievalWidget):
            self.flex_widget.load_state(state)

        self.save_annotation()
        self.mediator.set_position(0)

    @qtc.pyqtSlot()
    def load_manual_annotation(self):
        assert type(self.flex_widget) != QDisplaySample
        logging.info("LOADING MANUAL ANNOTATION")
        self.flex_widget = QDisplaySample()
        self.gui.set_right_widget(self.flex_widget)

        self.annotation_widget.samples_changed.connect(self.flex_widget.set_selected)

        self.mediator.stop_loop()

        if self.global_state is not None:
            self.load_state(self.global_state)

    @qtc.pyqtSlot()
    def load_retrieval_mode(self):
        assert type(self.flex_widget) != QRetrievalWidget
        logging.info("LOADING RETRIEVAL MODE")
        self.annotation_widget.samples_changed.disconnect(self.flex_widget.set_selected)

        self.flex_widget = QRetrievalWidget()
        self.gui.set_right_widget(self.flex_widget)

        self.flex_widget.start_loop.connect(self.mediator.start_loop)
        self.flex_widget.new_sample.connect(self.annotation_widget.new_sample)

        if self.global_state is not None:
            # self.load_state(self.global_state)
            self.flex_widget.load_state(self.global_state)

    def save_annotation(self):
        if self.global_state is None:
            logging.info("Nothing to save - annotation-object is None")
        else:
            logging.info("Saving current state")
            samples = self.annotation_widget.samples
            self.global_state.samples = samples
            for idx, x in enumerate(self.global_state.samples):
                logging.info(
                    "{}-Sample: ({}, {})".format(idx, x.start_position, x.end_position)
                )
            self.global_state.to_disk()

    @qtc.pyqtSlot()
    def settings_changed(self):
        settings = Settings.instance()
        app = qtw.QApplication.instance()

        custom_font = qtg.QFont()
        custom_font.setPointSize(settings.font)
        app.setFont(custom_font)

        FrameTimeMapper.instance().settings_changed()

        log_config_dict = filehandler.logging_config()
        log_config_dict["handlers"]["screen_handler"]["level"] = (
            "DEBUG" if settings.debugging_mode else "WARNING"
        )
        logging.config.dictConfig(log_config_dict)

        self.annotation_widget.settings_changed()

        toggle_stylesheet(settings.darkmode)


def toggle_stylesheet(darkmode):
    """
    Toggle the stylesheet to use the desired path in the Qt resource
    system (prefixed by `:/`) or generically (a path to a file on
    system).

    :path:      A full path to a resource or file on system
    """

    # get the QApplication instance,  or crash if not set
    app = qtw.QApplication.instance()
    if app is None:
        raise RuntimeError("No Qt Application found.")

    file = (
        qtc.QFile(":/dark/stylesheet.qss")
        if darkmode
        else qtc.QFile(":/light/stylesheet.qss")
    )
    file.open(qtc.QFile.ReadOnly | qtc.QFile.Text)
    stream = qtc.QTextStream(file)
    app.setStyleSheet(stream.readAll())


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def main():
    sys.excepthook = except_hook

    app = MainApplication(sys.argv)
    app.setStyle("Fusion")

    settings = Settings.instance()
    custom_font = qtg.QFont()
    custom_font.setPointSize(settings.font)
    app.setFont(custom_font)

    file = (
        qtc.QFile(":/dark/stylesheet.qss")
        if settings.darkmode
        else qtc.QFile(":/light/stylesheet.qss")
    )
    file.open(qtc.QFile.ReadOnly | qtc.QFile.Text)
    stream = qtc.QTextStream(file)
    app.setStyleSheet(stream.readAll())

    sys.exit(app.exec_())
