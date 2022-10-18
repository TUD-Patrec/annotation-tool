import time

import PyQt5.QtCore as qtc

from src.media.backend.player import AbstractMediaPlayer
from src.media.backend.queue import FairQueue


def time_in_millis():
    t = time.perf_counter()
    return int(t * 1000)


class Timer(qtc.QObject):
    timeout = qtc.pyqtSignal(AbstractMediaPlayer)
    set_position = qtc.pyqtSignal(AbstractMediaPlayer, int)
    finished = qtc.pyqtSignal()

    def init(self):
        # list of [subscriber, #updates]
        self.subscribers = []

        # queued subscribers
        self.queue = FairQueue()

        self.next_position = None
        self.open_position_updates = []

        self.open_timeouts = []
        self.MAX_OPEN_TIMEOUTS = 10

        self.ACTIVE_IDLE_TIME = 0.005
        self.PASSIVE_IDLE_TIME = 0.05

        self.active = True
        self.paused = True
        self.just_paused = False

        self.alpha = 1
        self.replay_speed = 1

        self.time = 0
        self.last_real_time_ms = None

    # Main-Loop
    def run(self):
        assert qtc.QThread.currentThread() is self.thread()
        self.init()
        self.last_real_time_ms = time_in_millis()

        while self.active:
            # Clearing the event_loop
            qtc.QCoreApplication.processEvents()

            # If there are set_position open tasks wait for all confirmations to arrive
            if self.open_position_updates:
                time.sleep(self.ACTIVE_IDLE_TIME)
                self._inner_reset()
                continue

            # Position update available - has priority
            if self.next_position is not None:
                self.change_position()
                continue

            # Paused -> Idle and wait for unpause
            if self.paused:
                if self.just_paused:
                    self.synchronize()
                    self.just_paused = False
                else:
                    if len(self.subscribers) > 1:
                        assert (
                            self.subscribers_in_sync()
                        ), "SUBSCRIBERS ARE OUT OF SYNC!"
                time.sleep(self.ACTIVE_IDLE_TIME)
                self._inner_reset()
                continue

            # No subscribers -> Idle and wait for subscribers
            if len(self.subscribers) == 0:
                time.sleep(self.PASSIVE_IDLE_TIME)
                self.reset()
                continue

            self.compute_time()
            self.update_queue()
            self.update_alpha()

            if (
                len(self.open_timeouts) < self.MAX_OPEN_TIMEOUTS
                and self.queue.has_elements()
            ):
                self.process_queue()
            else:
                time.sleep(self.ACTIVE_IDLE_TIME)

        # logging.info('*** Timer FINISHED ***')
        self.finished.emit()

    def subscribers_in_sync(self):
        if self.subscribers:
            main_subscriber = self.subscribers[0][0]
            fps_sync = self.subscribers[0][0].fps
            pos = main_subscriber.position

            for subscriber, _ in self.subscribers:
                fps = subscriber.fps
                if fps != fps_sync:
                    frame_rate_ratio = fps / fps_sync
                    pos_adjusted = int(frame_rate_ratio * pos)
                    if subscriber.position != pos_adjusted:
                        return False
                else:
                    if subscriber.position != pos:
                        return False
        return True

    def synchronize(self):
        if self.subscribers and self.next_position is None:
            pos = self.subscribers[0][0].position
            self.query_position_update(pos)

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def subscribe(self, x):
        assert qtc.QThread.currentThread() is self.thread()

        # Insert new subscriber with the count adjusted
        # to the current inner time of the timer
        r = 1000 / x.fps
        cnt = self.time / r
        self.subscribers.append([x, int(cnt)])

        # Wire signals
        self.timeout.connect(x.on_timeout)
        self.set_position.connect(x.set_position)
        x.ACK_timeout.connect(self.ACK_timeout)
        x.ACK_setpos.connect(self.ACK_setpos)

        self.synchronize()

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def unsubscribe(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        for idx in range(len(self.subscribers)):
            if self.subscribers[idx][0] is x:
                break
        else:
            raise RuntimeError

        # Unwire connections
        self.timeout.disconnect(x.on_timeout)
        self.set_position.disconnect(x.set_position)
        x.ACK_timeout.disconnect(self.ACK_timeout)
        x.ACK_setpos.disconnect(self.ACK_setpos)

        del self.subscribers[idx]
        self.queue.remove_item(x)

        # kinda hacky - but works
        for _ in range(len(self.open_timeouts)):
            self.ACK_timeout(x)

        for _ in range(len(self.open_position_updates)):
            self.ACK_setpos(x)

    @qtc.pyqtSlot()
    def reset(self):
        self.subscribers = []

        # queued subscribers
        self.queue = FairQueue()

        self.next_position = None
        self.open_position_updates = []

        self.open_timeouts = []

        self.just_paused = False

        self.alpha = 1

        self.time = 0
        self.last_real_time_ms = time_in_millis()

    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self.replay_speed = max(0.01, x)

    @qtc.pyqtSlot()
    def pause(self):
        self.setPaused(True)

    @qtc.pyqtSlot()
    def unpause(self):
        self.setPaused(False)

    @qtc.pyqtSlot(bool)
    def setPaused(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self.just_paused = x
        self.paused = x

    @qtc.pyqtSlot()
    def stop(self):
        assert qtc.QThread.currentThread() is self.thread()
        self.active = False

    @qtc.pyqtSlot(int)
    def query_position_update(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self.next_position = x

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def ACK_timeout(self, x):
        self.confirm(x, self.open_timeouts)

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def ACK_setpos(self, x):
        self.confirm(x, self.open_position_updates)

    def confirm(self, x, open_tasks):
        assert qtc.QThread.currentThread() is self.thread()
        for idx, l in enumerate(open_tasks):
            if x is l:
                del open_tasks[idx]
                return

    def _inner_reset(self):
        self.queue.clear()
        self.last_real_time_ms = time_in_millis()

    def compute_time(self):
        assert qtc.QThread.currentThread() is self.thread()
        current = time_in_millis()
        time_multiplier = self.replay_speed * self.alpha
        delta = int(time_multiplier * (current - self.last_real_time_ms))
        if delta > 0:
            self.time += delta
            self.last_real_time_ms = current

    def update_queue(self):
        assert qtc.QThread.currentThread() is self.thread()
        for idx, (subscriber, cnt) in enumerate(self.subscribers):
            old_cnt = cnt
            r = 1000 / (subscriber.fps)
            new_cnt = int(self.time / r)
            self.subscribers[idx][1] = new_cnt
            for _ in range(new_cnt - old_cnt):
                self.queue.push(subscriber)

    def process_queue(self):
        assert qtc.QThread.currentThread() is self.thread()
        while (
            len(self.open_timeouts) < self.MAX_OPEN_TIMEOUTS
            and self.queue.has_elements()
        ):
            subscriber = self.queue.pop()
            self.open_timeouts.append(subscriber)
            self.timeout.emit(subscriber)

    def update_alpha(self):
        assert qtc.QThread.currentThread() is self.thread()
        N = len(self.queue)
        THETA = min(len(self.subscribers) * 2, 5)
        # allow THETA queued timeouts without reducing speed,
        # offsettings some inconsistencies
        if N < THETA:
            self.alpha = 1
        else:
            MAX_QUEUE_LEN = 50
            EPSILON = 0.001
            self.alpha = max(EPSILON, 1 - (N - THETA) / (MAX_QUEUE_LEN - THETA))

    def change_position(self):
        assert qtc.QThread.currentThread() is self.thread()
        assert len(self.open_position_updates) == 0
        pos = self.next_position
        self.next_position = None

        for subscriber, _ in self.subscribers:
            self.open_position_updates.append(subscriber)
            self.set_position.emit(subscriber, pos)
