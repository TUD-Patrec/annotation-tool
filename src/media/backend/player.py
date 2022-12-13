from abc import abstractmethod
from enum import Enum

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.utility import filehandler


class UpdateReason(Enum):
    TIMEOUT = 1
    SETPOS = 2
    OFFSET = 3
    INIT = 4


class AbstractMediaPlayer(qtw.QWidget):
    remove_wanted = qtc.pyqtSignal(qtw.QWidget)  # Emit self to be removed
    new_input_wanted = qtc.pyqtSignal(str)  # Path to new input-file
    loaded = qtc.pyqtSignal(
        qtw.QWidget
    )  # Emit self to notify controller about successfully loading
    failed = qtc.pyqtSignal(
        qtw.QWidget
    )  # Emit self to notify controller about failed loading
    ACK_timeout = qtc.pyqtSignal(qtw.QWidget)  # Confirm timeout processed
    ACK_setpos = qtc.pyqtSignal(qtw.QWidget)  # Confirm set_position processed
    position_changed = qtc.pyqtSignal(int)  # Broadcast position after change
    cleaned_up = qtc.pyqtSignal(qtw.QWidget)

    def __init__(self, is_main, *args, **kwargs):
        super(AbstractMediaPlayer, self).__init__(*args, **kwargs)

        # media controll attributes
        self._fps = None
        self._N = None
        self._position = 0
        self._offset = 0
        self._play_forward = True

        # reference informations
        self._reference_fps = None
        self._reference_N = None

        self.setLayout(qtw.QHBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # distinct between primary player and added ones
        self._is_main_replay_widget = is_main

    def set_reference_player(self, p):
        self._reference_fps = p.fps
        self._reference_N = p.N

    def mousePressEvent(self, e):
        # rightclick = context_menu
        if e.button() == qtc.Qt.RightButton:
            self.open_context_menu()

    def open_context_menu(self):
        menu = qtw.QMenu(self)
        menu.addAction("Add another input source", self.add_input)

        if not self.is_main_replay_widget:
            menu.addAction("Remove input source", self.remove_input)

            menu.addAction("Adjust offset", self.adjust_offset)

        menu.popup(qtg.QCursor.pos())

    @qtc.pyqtSlot()
    def add_input(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            directory="", filter="Video MoCap (*.mp4 *.avi *.csv)"
        )
        if filehandler.is_non_zero_file(filename):
            self.new_input_wanted.emit(filename)

    @qtc.pyqtSlot()
    def remove_input(self):
        self.remove_wanted.emit(self)

    def change_offset(self, offs):
        self.offset = offs
        self.update_media_position(UpdateReason.OFFSET)

    @qtc.pyqtSlot()
    def adjust_offset(self):
        old_offset = self.offset
        input_dialog = qtw.QInputDialog()

        input_dialog.setInputMode(qtw.QInputDialog.IntInput)
        input_dialog.setIntRange(-(2**31), 2**31 - 1)
        input_dialog.intValueChanged.connect(self.change_offset)
        input_dialog.setIntValue(self.offset)
        input_dialog.setWindowTitle("Adjust offset")
        input_dialog.setLabelText("Offset")

        input_dialog.rejected.connect(lambda: self.change_offset(old_offset))

        self.inp_dia = input_dialog

        input_dialog.open()

    @abstractmethod
    @qtc.pyqtSlot(str)
    def load(self, input_file):
        raise NotImplementedError

    # TODO self.position + 1 needs to happen after the position update
    #  -> else while waiting for update the position
    # can get updated multiple times -> offsync
    @qtc.pyqtSlot(qtw.QWidget)
    def on_timeout(self, w):
        if self is w:
            if self.play_forward:
                if self.position + 1 < self.N_FRAMES():
                    self.position += 1
                    self.confirm_update(UpdateReason.TIMEOUT)  # TODO fix
                    self.update_media_position(UpdateReason.SETPOS)  # TODO fix
                else:
                    self.confirm_update(UpdateReason.TIMEOUT)
            else:
                if self.position > 0:
                    self.position -= 1
                    self.confirm_update(UpdateReason.TIMEOUT)
                    self.update_media_position(UpdateReason.SETPOS)
                else:
                    self.confirm_update(UpdateReason.TIMEOUT)

    @qtc.pyqtSlot(qtw.QWidget, int)
    def set_position(self, w, new_pos):
        if self is w:
            new_pos = self.translate_frame_position(new_pos)

            if new_pos != self.position:
                self.position = new_pos
                self.update_media_position(UpdateReason.SETPOS)
            else:
                # Short circuting if no position change has happened
                self.confirm_update(UpdateReason.SETPOS)

    @qtc.pyqtSlot()
    def ack_timeout(self):
        self.ACK_timeout.emit(self)

    @qtc.pyqtSlot()
    def ack_position_update(self):
        self.ACK_setpos.emit(self)

    def N_FRAMES(self):
        if self._is_main_replay_widget:
            N = self.n_frames
        else:
            assert self._reference_fps is not None
            assert self._reference_N is not None
            N = min(self.translate_frame_position(self._reference_N), self.n_frames)
        return N

    def translate_frame_position(self, x):
        if self._is_main_replay_widget:
            return x
        else:
            return int(x * self.fps / self._reference_fps)

    def send_ACK(self, r):
        if r == UpdateReason.TIMEOUT:
            self.ACK_timeout.emit(self)
        if r == UpdateReason.SETPOS:
            self.ACK_setpos.emit(self)

    def confirm_update(self, update_reason):
        self.send_ACK(update_reason)
        if update_reason == UpdateReason.TIMEOUT:
            self.emit_position()

    def emit_position(self):
        if self._is_main_replay_widget:
            assert (
                self.offset == 0
            )  # offset must not be changed for the main replay widget
            assert 0 <= self.position < self.n_frames
            self.position_changed.emit(self.position)

    @abstractmethod
    def update_media_position(self, reason: UpdateReason):
        raise NotImplementedError

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        assert 0 < x
        self._fps = x

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        assert 0 <= x
        self._position = x

    @property
    def n_frames(self):
        return self._N

    @n_frames.setter
    def n_frames(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        assert 0 <= x
        self._N = x

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self._offset = x

    @property
    def play_forward(self):
        assert qtc.QThread.currentThread() is self.thread()
        return self._play_forward

    @play_forward.setter
    def play_forward(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self._play_forward = x

    @property
    def is_main_replay_widget(self):
        return self._is_main_replay_widget

    @property
    def reference_fps(self):
        return self._reference_fps

    @property
    def reference_N(self):
        return self._reference_N
