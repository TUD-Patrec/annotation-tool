import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from .backend.controller import QMediaMainController


class QMediaWidget(qtw.QWidget):
    """
    A simple facade, forwarding all necessary slots and signals
    between the main-application and the media-backend.

    Signals:
        position_changed
            Transports the current position of the main replaysource
            (always the leftmost on the screen)
        cleanedUp
            Signals that all sub widgets and threads have been shutdown successfully.

    Slots:
        load
           Expects an Annotation-instance
        set_position
            Updates the current displayed frame
        play
            Starts running the media
        pause
            Pauses the media
        set_replay_speed
            Updates how fast the media is played
        settings_changed
            Needed for updating FPS of Media
        shutdown
            Cleans up all threads and subwidgets
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
