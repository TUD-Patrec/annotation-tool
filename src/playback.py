import logging

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from .qt_helper_widgets.lines import QHLine
from .utility.functions import FrameTimeMapper


class QPlaybackWidget(qtw.QWidget):
    playing = qtc.pyqtSignal()
    paused = qtc.pyqtSignal()
    skip_frames = qtc.pyqtSignal(bool, bool)
    replay_speed_changed = qtc.pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        self.n_frames = 0

        super(QPlaybackWidget, self).__init__(*args, **kwargs)
        back_button = qtw.QAction("back", self)
        back_button.setStatusTip("back")
        back_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_MediaSkipBackward))
        back_button.triggered.connect(lambda _: self.skip_frames.emit(False, True))
        self.back_button = back_button

        slow_back_button = qtw.QAction("slow_back", self)
        slow_back_button.setStatusTip("slow_back")
        slow_back_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_ArrowBack))
        slow_back_button.triggered.connect(
            lambda _: self.skip_frames.emit(False, False)
        )
        self.slow_back_button = slow_back_button

        play_stop_button = qtw.QAction("play_stop", self)
        play_stop_button.setText("Start")
        play_stop_button.setStatusTip("play_stop")
        play_stop_button.setCheckable(True)
        play_stop_button.setIcon(self.style().standardIcon(qtw.QStyle.SP_MediaPlay))
        play_stop_button.triggered.connect(lambda _: self.play_stop_clicked())
        self.play_stop_button = play_stop_button

        slow_forward_button = qtw.QAction("slow_forward", self)
        slow_forward_button.setStatusTip("slow_forward")
        slow_forward_button.setIcon(
            self.style().standardIcon(qtw.QStyle.SP_ArrowForward)
        )
        slow_forward_button.triggered.connect(
            lambda _: self.skip_frames.emit(True, False)
        )
        self.slow_forward_button = slow_forward_button

        forward_button = qtw.QAction("forward", self)
        forward_button.setStatusTip("forward")
        forward_button.setIcon(
            self.style().standardIcon(qtw.QStyle.SP_MediaSkipForward)
        )
        forward_button.triggered.connect(lambda _: self.skip_frames.emit(True, True))
        self.forward_button = forward_button

        self.replay_speed_widget = QReplaySpeedSlider(self)
        self.replay_speed_widget.valueChanged.connect(
            lambda x: self.replay_speed_changed.emit(x / 100)
        )

        self.lbl = qtw.QLabel("0\n0")
        self.lbl.setAlignment(qtc.Qt.AlignCenter)

        self.toolbar = qtw.QToolBar("SomeTitle", self)
        self.toolbar.setOrientation(qtc.Qt.Vertical)

        self.toolbar.addAction(back_button)
        self.toolbar.addAction(slow_back_button)
        self.toolbar.addAction(play_stop_button)
        self.toolbar.addAction(slow_forward_button)
        self.toolbar.addAction(forward_button)

        vbox = qtw.QVBoxLayout(self)
        vbox.addWidget(self.toolbar, stretch=1, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(qtw.QLabel("Replay\nSpeed"))
        vbox.addWidget(self.replay_speed_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(qtw.QLabel("Position"))
        vbox.addWidget(self.lbl)
        self.setLayout(vbox)

    @qtc.pyqtSlot(int)
    def set_position(self, x):
        self.update_label(x, self.n_frames)

    def update_label(self, pos, limit):
        frame_time_mapper = FrameTimeMapper.instance()
        position = frame_time_mapper.frame_repr(pos)
        limit = frame_time_mapper.frame_repr(max(0, limit - 1))
        self.lbl.setText("{}\n{}".format(position, limit))

    def play_stop_clicked(self):
        playing = self.play_stop_button.isChecked()
        icon_ = qtw.QStyle.SP_MediaPause if playing else qtw.QStyle.SP_MediaPlay
        self.play_stop_button.setIcon(self.style().standardIcon(icon_))
        if playing:
            self.playing.emit()
        else:
            self.paused.emit()

    @qtc.pyqtSlot()
    def reset(self):
        self.pause()
        self.replay_speed_widget.current = 100
        self.replay_speed_widget.plus_step()

    @qtc.pyqtSlot()
    def play(self):
        playing = self.play_stop_button.isChecked()
        if not playing:
            self.play_stop_button.trigger()

    @qtc.pyqtSlot()
    def pause(self):
        playing = self.play_stop_button.isChecked()
        if playing:
            self.play_stop_button.trigger()

    def increase_speed(self):
        self.replay_speed_widget.plus_step()

    def decrease_speed(self):
        self.replay_speed_widget.minus_step()


class QReplaySpeedSlider(qtw.QSlider):
    def __init__(self, *args, **kwargs):
        super(QReplaySpeedSlider, self).__init__(*args, **kwargs)
        self.setMinimum(10)
        self.setMaximum(100)
        self.setSingleStep(10)
        self.setTickInterval(10)

        self.setTickPosition(qtw.QSlider.TicksLeft)
        self.setValue(100)

    def plus_step(self):
        new_value = min(self.maximum(), self.value() + 10)
        self.setValue(new_value)
        logging.info(self.value())
        self.valueChanged.emit(self.value())

    def minus_step(self):
        new_value = max(self.minimum(), self.value() - 10)
        self.setValue(new_value)
        logging.info(self.value())
        self.valueChanged.emit(self.value())
