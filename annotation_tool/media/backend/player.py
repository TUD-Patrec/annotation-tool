from abc import abstractmethod

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.utility import filehandler


class AbstractMediaPlayer(qtw.QWidget):
    remove_wanted = qtc.pyqtSignal(qtw.QWidget)  # Emit self to be removed
    new_input_wanted = qtc.pyqtSignal(str)  # Path to new input-file
    loaded = qtc.pyqtSignal(
        qtw.QWidget
    )  # Emit self to notify controller about successfully loading
    failed = qtc.pyqtSignal(
        qtw.QWidget
    )  # Emit self to notify controller about failed loading
    cleaned_up = qtc.pyqtSignal(qtw.QWidget)
    finished = qtc.pyqtSignal(qtw.QWidget)

    def __init__(self, is_main, *args, **kwargs):
        super(AbstractMediaPlayer, self).__init__(*args, **kwargs)

        self._terminated = False

        # media controll attributes
        self._fps = None
        self._N = None
        self._position = 0
        self._offset = 0
        self._play_forward = True

        self.setLayout(qtw.QHBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # distinct between primary player and added ones
        self._is_main_replay_widget = is_main

    def contextMenuEvent(self, e):
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
        self.update_media_position()

    @qtc.pyqtSlot()
    def adjust_offset(self):
        old_offset = self.offset
        input_dialog = qtw.QInputDialog(self)

        input_dialog.setInputMode(qtw.QInputDialog.InputMode.IntInput)
        input_dialog.setIntRange(-(2**31), 2**31 - 1)
        input_dialog.intValueChanged.connect(self.change_offset)
        input_dialog.setIntValue(self.offset)
        input_dialog.setWindowTitle("Adjust offset")
        input_dialog.setLabelText("Offset")

        input_dialog.rejected.connect(lambda: self.change_offset(old_offset))

        input_dialog.open()

    @abstractmethod
    @qtc.pyqtSlot(str)
    def load(self, input_file):
        raise NotImplementedError

    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        if new_pos != self.position:
            self.position = new_pos
            self.update_media_position()

    @qtc.pyqtSlot()
    def shutdown(self):
        self.terminated = True
        self.finished.emit(self)

    def kill(self):
        pass

    @abstractmethod
    def update_media_position(self):
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
    def is_main_replay_widget(self):
        return self._is_main_replay_widget

    @property
    def terminated(self):
        return self._terminated

    @terminated.setter
    def terminated(self, x):
        self._terminated = x
