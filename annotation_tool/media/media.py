import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw

from .backend.controller import QMediaMainController


class QMediaWidget(qtw.QWidget):
    """
    A simple facade, forwarding all necessary slots and signals
    between the main-application and the media-backend.

    Signals:
        position_changed
            Transports the current position of the main replay source
            (always the leftmost on the screen)

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
    loaded = qtc.pyqtSignal()
    additional_media_changed = qtc.pyqtSignal(list)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.controller = QMediaMainController()
        self.controller.timeout.connect(self.position_changed)
        self.controller.additional_media_changed.connect(self.additional_media_changed)
        self.controller.loaded.connect(self.loaded)
        self._layout = qtw.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.controller)

    @qtc.pyqtSlot(str, list)
    def load(self, file, additional_media=[]):
        self.controller.load(file, additional_media)

    @qtc.pyqtSlot(list)
    def set_additional_media(self, files):
        for f in files:
            self.controller.add_replay_widget(f)

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
