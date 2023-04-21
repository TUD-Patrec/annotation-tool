import time

import PyQt6.QtCore as qtc


def time_in_millis():
    return int(time.perf_counter() * 1000)


class Synchronizer(qtc.QObject):
    finished = qtc.pyqtSignal()
    position_changed = qtc.pyqtSignal(qtc.QObject, int)
    timeout = qtc.pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self._subscribers = []

        self._start_time = None
        self._start_pos = 0
        self._last_timeout_pos = -1

        self._replay_speed = 1

        self._active = True
        self._paused = True

        self._timer_interval = 5  # check every 5 ms for updates
        self._timer = qtc.QTimer(self)
        self._timer.timeout.connect(self.handle_timeout)

    @property
    def reference_widget(self):
        for subscriber in self._subscribers:
            if subscriber.main_replay_widget:
                return subscriber
        return None

    @property
    def fps(self):
        return 0 if self.reference_widget is None else self.reference_widget.fps

    @property
    def frame_position(self):
        if self.reference_widget:
            if not self._start_time or self._paused:
                # return the last known position

                return self.reference_widget.position
            else:
                # calculate the position based on the current time

                delta_t = (
                    time_in_millis() - self._start_time
                ) * self._replay_speed  # ms
                delta_pos = int(delta_t * self.fps / 1000)  # frames
                new_pos = self._start_pos + delta_pos
                return min(
                    new_pos, self.reference_widget.n_frames - 1
                )  # do not go beyond the end
        else:
            # no reference widget, so we cannot calculate the position

            return 0

    @qtc.pyqtSlot()
    def handle_timeout(self):
        is_valid = (
            self.reference_widget is not None and self._active and not self._paused
        )
        if is_valid:
            self.update_positions(from_timeout=True)

    def update_positions(self, from_timeout=False, new_pos=None):
        is_valid = self.reference_widget is not None and self._active
        if not is_valid:
            return

        if new_pos is None:
            new_pos = self.frame_position

        assert 0 <= new_pos <= self.reference_widget.n_frames - 1  # sanity check

        for subscriber in self._subscribers:
            target_pos = new_pos  # target position in the subscriber's fps

            if subscriber.fps != self.fps:
                target_pos *= (
                    subscriber.fps / self.fps
                )  # scale to the fps of the subscriber
                target_pos = int(target_pos)

            if target_pos != subscriber.position:
                self.position_changed.emit(
                    subscriber, target_pos
                )  # Update the displaying widgets

            if (
                subscriber.main_replay_widget
                and from_timeout
                and target_pos != self._last_timeout_pos
            ):
                self._last_timeout_pos = target_pos
                self.timeout.emit(
                    target_pos
                )  # Update the rest of the app (e.g. the timeline)

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
        self._start_time = None

    @qtc.pyqtSlot()
    def unpause(self):
        self._paused = False
        self.sync_time()
        self._timer.start(self._timer_interval)

    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self._replay_speed = max(0.01, x)
        self.sync_time()

    @qtc.pyqtSlot(int)
    def set_position(self, x):
        self.sync_time()
        self.update_positions(from_timeout=False, new_pos=x)

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
        self._start_time = None
        self._subscribers = []
        self.timeout.emit(
            0
        )  # Overwrite outdated timeouts from previous replay, could be handled somewhere else

    @qtc.pyqtSlot(qtc.QObject)
    def subscribe(self, subscriber):
        if subscriber.main_replay_widget and self.reference_widget is not None:
            raise ValueError(
                "Only one main replay widget allowed, but {} and {} are both marked as main".format(
                    self.reference_widget, subscriber
                )
            )
        self._subscribers.append(subscriber)

        self.position_changed.connect(subscriber.set_position_)
        self.update_positions()

    @qtc.pyqtSlot(qtc.QObject)
    def unsubscribe(self, subscriber):
        self._subscribers = [x for x in self._subscribers if x != subscriber]
        self.position_changed.disconnect(subscriber.set_position_)

    def sync_time(self):
        self._start_pos = self.frame_position
        self._start_time = time_in_millis() if not self._paused else None
