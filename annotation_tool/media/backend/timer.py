import logging
import time

import PyQt6.QtCore as qtc
import numpy as np


def time_in_millis():
    return int(time.perf_counter() * 1000)


class RingBuf:
    def __init__(self, size=50):
        self._size = size
        self._buf = np.zeros(size)
        self._pos = 0

    def append(self, item):
        self._buf[self._pos] = item
        self._pos = (self._pos + 1) % self._size

    def avg(self):
        return sum(self._buf) / self._size

    def max(self):
        return np.max(self._buf)

    def min(self):
        return np.min(self._buf)


class Synchronizer(qtc.QObject):
    finished = qtc.pyqtSignal()
    position_changed = qtc.pyqtSignal(qtc.QObject, int)
    timeout = qtc.pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self._subscribers = []

        self._start_time = None
        self._pos = 0
        self._last_pos = 0
        self._last_timeout_pos = -1

        self._replay_speed = 1
        self._fps = 60

        self._active = True
        self._paused = True

        self._timer_interval = 5  # check every 5 ms for updates
        self._timer = qtc.QTimer(self)
        self._timer.timeout.connect(self.handle_timeout)

        # evaluation
        self._last_timeout = time_in_millis()
        self._timer_interval_buf = RingBuf(100)
        self._notify_interval = 250
        self._notify = 1

    @qtc.pyqtSlot()
    def handle_timeout(self):
        if not self._active:
            return
        if len(self._subscribers) == 0:
            return
        if self._paused:
            return

        now = time_in_millis()
        self._timer_interval_buf.append(now - self._last_timeout)
        self._last_timeout = now

        if self._notify % self._notify_interval == 0:
            logging.debug(
                f"timer interval: {self._timer_interval_buf.avg():.2f} ms, max: {self._timer_interval_buf.max():.2f} ms, min: {self._timer_interval_buf.min():.2f} ms"
            )
        self._notify += 1

        self.update_positions(from_timeout=True)

    def update_positions(self, from_timeout=True, force=False):
        if self._active:
            fps = self._fps
            abs_pos = self.frame_position

            if abs_pos == self._last_pos and not force:
                return

            for subscriber in self._subscribers:
                new_pos = int(abs_pos * subscriber.fps / fps)

                if new_pos != subscriber.position or force:
                    self.position_changed.emit(
                        subscriber, new_pos
                    )  # Update the displaying widgets

                if (
                    subscriber.main_replay_widget
                    and from_timeout
                    and new_pos != self._last_timeout_pos
                ):
                    self._last_timeout_pos = new_pos
                    self.timeout.emit(
                        new_pos
                    )  # Update the rest of the app (e.g. the timeline)

            self._last_pos = abs_pos

    @qtc.pyqtSlot(bool)
    def set_paused(self, paused):
        if paused:
            self.pause()
        else:
            self.unpause()

    @qtc.pyqtSlot()
    def pause(self):
        self._timer.stop()
        self._paused = True
        self._pos = self.frame_position
        self._start_time = None

    @qtc.pyqtSlot()
    def unpause(self):
        self._paused = False
        self._start_time = time_in_millis()
        self._timer.start(self._timer_interval)

    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.sync_position()
        self._replay_speed = max(0.01, x)

    @qtc.pyqtSlot(int)
    def set_position(self, x):
        fps = 0
        for subscriber in self._subscribers:
            if subscriber.main_replay_widget:
                fps = subscriber.fps
                break
        pos_adjusted = int(x * self._fps / fps) if fps > 0 else x
        self._pos = pos_adjusted
        self._start_time = time_in_millis() if not self._paused else None
        self.update_positions(from_timeout=False)

    @qtc.pyqtSlot()
    def stop(self):
        self._active = False
        self._timer.stop()
        self._timer.deleteLater()
        self._timer = None
        self.finished.emit()

    @qtc.pyqtSlot()
    def reset(self):
        self._timer.stop()
        self._paused = True
        self._pos = 0
        self._last_pos = 0
        self._start_time = None
        self._subscribers = []
        self.timeout.emit(
            0
        )  # Overwrite outdated timeouts from previous replay, could be handled somewhere else

    @qtc.pyqtSlot(qtc.QObject)
    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)
        self.position_changed.connect(subscriber.set_position_)
        self.update_positions(from_timeout=False, force=True)

    @qtc.pyqtSlot(qtc.QObject)
    def unsubscribe(self, subscriber):
        self._subscribers = [x for x in self._subscribers if x != subscriber]
        self.position_changed.disconnect(subscriber.set_position_)

    @property
    def frame_position(self):
        if self._start_time is None:
            return self._pos
        elapsed = self._replay_speed * (time_in_millis() - self._start_time)
        return int(self._pos + elapsed * self._fps / 1000)

    def sync_position(self):
        self._pos = self.frame_position
        self._start_time = time_in_millis() if not self._paused else None
