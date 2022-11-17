"""

Synchronization between all kinds of different widgets is getting too complicated to be
solved inside the main_controller.
This module is meant to abstract all the tasks which need to happen in the background.

"""

import PyQt5.QtCore as qtc

from src.annotation.controller import AnnotationController
from src.annotation.timeline import QTimeLine
from src.media.media import QMediaWidget
from src.playback import QPlaybackWidget
from src.settings import settings


class Mediator(qtc.QObject):
    def __init__(self):
        super(Mediator, self).__init__()
        self.position = 0
        self.n_frames = 0
        self.upper = None
        self.lower = None

        self.receivers = []
        self.emitters = []

    def add_receiver(self, receiver):
        assert isinstance(
            receiver, (QTimeLine, QMediaWidget, AnnotationController, QPlaybackWidget)
        )
        if receiver not in self.receivers:
            self.receivers.append(receiver)

    def remove_receiver(self, receiver):
        self.receivers.remove(receiver)
        assert receiver not in self.receivers

    def add_emitter(self, emitter):
        assert isinstance(emitter, (QMediaWidget, QTimeLine, QPlaybackWidget))
        if isinstance(emitter, QMediaWidget):
            emitter.position_changed.connect(self.on_timeout)
        elif isinstance(emitter, QTimeLine):
            emitter.position_changed.connect(self.set_position)
        elif isinstance(emitter, QPlaybackWidget):
            emitter.skip_frames.connect(self.skip_frames)
        self.emitters.append(emitter)

    def remove_emitter(self, emitter):
        assert isinstance(emitter, (QMediaWidget, QTimeLine, QPlaybackWidget))
        if isinstance(emitter, QMediaWidget):
            emitter.position_changed.disconnect(self.on_timeout)
        elif isinstance(emitter, QTimeLine):
            emitter.position_changed.disconnect(self.set_position)
        elif isinstance(emitter, QPlaybackWidget):
            emitter.skip_frames.disconnect(self.skip_frames)
        self.emitters.remove(emitter)
        assert emitter not in self.emitters

    @qtc.pyqtSlot(int)
    def set_position(self, x, force_update=False):
        check1 = (0 <= x < self.n_frames) or (x == 0 == self.n_frames)
        check2 = x != self.position or force_update
        if check1 and check2:
            if self.looping:
                x = min(self.upper, max(self.lower, x))
            self.position = x
            for rec in self.receivers:
                rec.set_position(x)

    @qtc.pyqtSlot(int)
    def on_timeout(self, x):
        assert (0 <= x < self.n_frames) or (x == 0 == self.n_frames)

        # Filter valid timeouts -> remove outdated ones
        if x == self.position + 1:
            if self.looping and x >= self.upper:
                self.set_position(self.lower)
                return
            # only update non-mediaWidgets
            self.position += 1
            for rec in self.receivers:
                if not isinstance(rec, QMediaWidget):
                    rec.set_position(self.position)
        else:
            # logging.debug(f"Filtered outdated update = {x = }")
            pass

    @qtc.pyqtSlot(bool, bool)
    def skip_frames(self, forward_step, fast):
        n = settings.big_skip if fast else settings.small_skip
        if not forward_step:
            n *= -1

        new_pos = max(0, min(self.n_frames - 1, self.position + n))
        self.set_position(new_pos)

    @qtc.pyqtSlot(int, int)
    def start_loop(self, lower, upper):
        assert 0 <= lower
        assert lower <= upper
        assert upper < self.n_frames
        self.lower = lower
        self.upper = upper
        self.set_position(lower)

    @qtc.pyqtSlot()
    def stop_loop(self):
        self.upper = None
        self.lower = None

    @property
    def looping(self):
        return self.upper is not None and self.lower is not None
