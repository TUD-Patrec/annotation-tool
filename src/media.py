import logging

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

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

    positionChanged = qtc.pyqtSignal(int)
    cleanedUp = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.controller = QMediaMainController()
        self.controller.cleaned_up.connect(self.cleanedUp)
        self.controller.position_changed.connect(self.positionChanged)
        self._layout = qtw.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.controller)

    @qtc.pyqtSlot(object)
    def loadAnnotation(self, o):
        self.endLoop()
        self.controller.load_annotation(o)

    def load_initial_view(self):
        self.setPosition(0)

    @qtc.pyqtSlot(int)
    def setPosition(self, p):
        self.controller.set_position(p)

    def getPosition(self):
        if self.controller.replay_widgets:
            return self.controller.replay_widgets[0].position
        else:
            return -1

    @qtc.pyqtSlot()
    def play(self):
        self.controller.play()

    @qtc.pyqtSlot()
    def pause(self):
        self.controller.pause()

    @qtc.pyqtSlot(float)
    def setReplaySpeed(self, x):
        self.controller.set_replay_speed(x)

    @qtc.pyqtSlot()
    def settingsChanges(self):
        self.controller.settings_changed()

    @qtc.pyqtSlot()
    def shutdown(self):
        self.controller.shutdown()

    @qtc.pyqtSlot(int, int)
    def startLoop(self, x, y):
        logging.info(f"STARTING LOOP {x=}, {y=}")
        self.controller.start_loop_slot(x, y)

    @qtc.pyqtSlot()
    def endLoop(self):
        self.controller.end_loop_slot()
