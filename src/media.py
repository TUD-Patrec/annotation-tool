import logging

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from .media_backend.controller import QMediaMainController


class QMediaWidget(qtw.QWidget):
    """
    A simple facade, forwarding all necessary slots and signals between the main-application and the media-backend.

    Signals:
           positionChanged: Transports the current position of the main replaysource (always the leftmost on the screen)
           cleanedUp: Signals that all sub widgets and threads have been shutdown successfully. Should be waited for befor exiting the app.

    Slots:
           load_annotation: Expects a Annotation-instance
           setPosition: Updates the current displayed frame
           play: Starts running the media
           pause: Pauses the media
           setReplaySpeed: Updates how fast the media is played
           settingsChanged: Needed for updating FPS of Media, which itself does not contain information about its refresh-rate
           shutdown: Cleans up all threads and subwidgets
           startLoop: Starts looping the video-segment within the specified interval
           endLoop: Stops looping
    """

    position_changed = qtc.pyqtSignal(int)
    cleanedUp = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.controller = QMediaMainController()
        self.controller.cleaned_up.connect(self.cleanedUp)
        self.controller.position_changed.connect(self.position_changed)
        self._layout = qtw.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.controller)

    @qtc.pyqtSlot(str)
    def load(self, file):
        self.controller.load(file)

    @qtc.pyqtSlot(int)
    def set_position(self, p):
        self.controller.set_position(p)

    @qtc.pyqtSlot()
    def play(self):
        self.controller.play()

    @qtc.pyqtSlot()
    def pause(self):
        self.controller.pause()

    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.controller.set_replay_speed(x)

    @qtc.pyqtSlot()
    def settings_changed(self):
        self.controller.settings_changed()

    @qtc.pyqtSlot()
    def shutdown(self):
        self.controller.shutdown()
