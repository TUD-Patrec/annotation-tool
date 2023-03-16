import enum

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.user_actions import ReplayActions
from annotation_tool.utility.resources import *  # noqa: F403, F401

from .qt_helper_widgets.lines import QHLine
from .qt_helper_widgets.own_slider import OwnSlider


class QPlaybackWidget(qtw.QWidget):
    playing = qtc.pyqtSignal()
    paused = qtc.pyqtSignal()
    skip_frames = qtc.pyqtSignal(bool, bool)
    replay_speed_changed = qtc.pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        self.n_frames = 0

        self.play_icon = qtg.QIcon(qtg.QPixmap(":/play_icon.png"))
        self.pause_icon = qtg.QIcon(qtg.QPixmap(":/pause_icon.png"))
        self.skip_forward_icon = qtg.QIcon(qtg.QPixmap(":/skip_next_icon.png"))
        self.skip_backward_icon = qtg.QIcon(qtg.QPixmap(":/skip_previous_icon.png"))
        self.skip_backward_fast_icon = qtg.QIcon(
            qtg.QPixmap(":/skip_previous_2_icon.png")
        )
        self.skip_forward_fast_icon = qtg.QIcon(qtg.QPixmap(":/skip_next_2_icon.png"))

        super(QPlaybackWidget, self).__init__(*args, **kwargs)
        back_button = qtg.QAction("Skip backward (fast)", self)
        back_button.setStatusTip("Skip backward (fast)")
        back_button.setIcon(self.skip_backward_fast_icon)
        back_button.triggered.connect(lambda _: self.skip_frames.emit(False, True))
        self.back_button = back_button

        slow_back_button = qtg.QAction("Skip backward", self)
        slow_back_button.setStatusTip("Skip backward")
        slow_back_button.setIcon(self.skip_backward_icon)
        slow_back_button.triggered.connect(
            lambda _: self.skip_frames.emit(False, False)
        )
        self.slow_back_button = slow_back_button

        play_stop_button = qtg.QAction("Play/Pause", self)
        play_stop_button.setText("Start")
        play_stop_button.setStatusTip("Play/Pause")
        play_stop_button.setCheckable(True)
        play_stop_button.setIcon(self.play_icon)

        play_stop_button.triggered.connect(lambda _: self.play_stop_clicked())
        self.play_stop_button = play_stop_button

        slow_forward_button = qtg.QAction("Skip forward", self)
        slow_forward_button.setStatusTip("Skip forward")
        slow_forward_button.setIcon(self.skip_forward_icon)
        slow_forward_button.triggered.connect(
            lambda _: self.skip_frames.emit(True, False)
        )
        self.slow_forward_button = slow_forward_button

        forward_button = qtg.QAction("Skip forward (fast)", self)
        forward_button.setStatusTip("Skip forward (fast)")
        forward_button.setIcon(self.skip_forward_fast_icon)
        forward_button.triggered.connect(lambda _: self.skip_frames.emit(True, True))
        self.forward_button = forward_button

        self.replay_speed_widget = SliderWidget(self)
        self.replay_speed_widget.valueChanged.connect(
            lambda x: self.replay_speed_changed.emit(x / 100)
        )

        self.lbl = qtw.QLabel("0\n0")
        self.lbl.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)

        self.toolbar = qtw.QToolBar("SomeTitle", self)
        self.toolbar.setOrientation(qtc.Qt.Orientation.Vertical)

        self.toolbar.addAction(back_button)
        self.toolbar.addAction(slow_back_button)
        self.toolbar.addAction(play_stop_button)
        self.toolbar.addAction(slow_forward_button)
        self.toolbar.addAction(forward_button)

        vbox = qtw.QVBoxLayout(self)
        vbox.addWidget(
            self.toolbar, stretch=1, alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )
        vbox.addWidget(
            qtw.QLabel("Replay\nSpeed"), alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )
        vbox.addWidget(
            self.replay_speed_widget, alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )
        vbox.addWidget(QHLine())
        vbox.addWidget(
            qtw.QLabel("Position"), alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )
        vbox.addWidget(self.lbl, alignment=qtc.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(vbox)

    @qtc.pyqtSlot(int)
    def set_position(self, x):
        self.update_label(x, self.n_frames)

    def update_label(self, pos, limit):
        limit = max(0, limit - 1)
        self.lbl.setText("{}\n{}".format(pos, limit))

    def play_stop_clicked(self):
        playing = self.play_stop_button.isChecked()
        icon_ = self.pause_icon if playing else self.play_icon
        self.play_stop_button.setIcon(icon_)
        self.play_stop_button.setText("Pause" if playing else "Start")
        if playing:
            self.playing.emit()
        else:
            self.paused.emit()

    @qtc.pyqtSlot()
    def reset(self):
        self.pause()
        self.replay_speed_widget.reset_slider()

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

    def skip_forward(self):
        self.skip_frames.emit(True, False)

    def skip_backward(self):
        self.skip_frames.emit(False, False)

    def skip_forward_fast(self):
        self.skip_frames.emit(True, True)

    def skip_backward_fast(self):
        self.skip_frames.emit(False, True)

    @qtc.pyqtSlot(enum.Enum)
    def on_user_action(self, action: ReplayActions):
        d = {
            ReplayActions.PLAY_OR_PAUSE: self.play_stop_button.trigger,
            ReplayActions.SKIP_FRAMES: self.skip_forward,
            ReplayActions.SKIP_FRAMES_FAR: self.skip_forward_fast,
            ReplayActions.SKIP_FRAMES_BACK: self.skip_backward,
            ReplayActions.SKIP_FRAMES_BACK_FAR: self.skip_backward_fast,
            ReplayActions.INCREASE_SPEED: self.increase_speed,
            ReplayActions.DECREASE_SPEED: self.decrease_speed,
        }
        if action in d:
            d[action]()


class SliderWidget(qtw.QWidget):
    valueChanged = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(SliderWidget, self).__init__(*args, **kwargs)
        self.label = qtw.QLabel("100")
        self.label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)

        self.slider = OwnSlider()
        self.slider.setOrientation(qtc.Qt.Orientation.Horizontal)
        self.slider.setRange(2, 40)
        self.slider.setTickPosition(qtw.QSlider.TickPosition.TicksBelow)
        self.slider.setSingleStep(1)
        self.slider.setTickInterval(5)
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.setValue(20)

        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.label)

    @qtc.pyqtSlot(int)
    def slider_changed(self, value):
        value = value * 5  # 5% steps
        self.label.setText(f"{value}%")
        self.valueChanged.emit(value)

    @qtc.pyqtSlot()
    def reset_slider(self):
        self.slider.setValue(20)

    @qtc.pyqtSlot()
    def plus_step(self):
        self.slider.plus_step()

    @qtc.pyqtSlot()
    def minus_step(self):
        self.slider.minus_step()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.plus_step()
        else:
            self.minus_step()
