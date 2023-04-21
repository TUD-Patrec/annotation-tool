import enum
import logging

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.media.backend.player import AbstractMediaPlayer
from annotation_tool.media.backend.timer import Synchronizer
from annotation_tool.media.backend.type_specific_player.mocap import MocapPlayer
from annotation_tool.media.backend.type_specific_player.video import VideoPlayer
from annotation_tool.media_reader import media_type_of

media_proxy_map = {}


class MediaProxy(qtc.QObject):
    ACK_timeout: qtc.pyqtSignal = qtc.pyqtSignal(qtc.QObject)
    ACK_setpos: qtc.pyqtSignal = qtc.pyqtSignal(qtc.QObject)
    set_position = qtc.pyqtSignal(int)
    timeout = qtc.pyqtSignal()

    def __init__(self, media_widget: AbstractMediaPlayer):
        super().__init__()
        self.set_position.connect(media_widget.set_position)

        media_proxy_map[id(media_widget)] = self
        self.media_widget = media_widget

        self._fps = media_widget.fps

    @qtc.pyqtSlot(qtc.QObject, int)
    def set_position_(self, proxy, position):
        if proxy is self:
            self.set_position.emit(position)

    @property
    def position(self):
        return self.media_widget.position

    @property
    def fps(self):
        return self._fps

    @property
    def n_frames(self):
        return self.media_widget.n_frames

    @property
    def main_replay_widget(self):
        return self.media_widget._is_main_replay_widget


class MediaState(enum.Enum):
    LOADING = 0
    AVAILABLE = 1


class QMediaMainController(qtw.QWidget):
    timeout = qtc.pyqtSignal(int)
    query_position_update = qtc.pyqtSignal(int)
    setPaused = qtc.pyqtSignal(bool)
    stop = qtc.pyqtSignal()
    replay_speed_changed = qtc.pyqtSignal(float)
    subscribe = qtc.pyqtSignal(qtc.QObject)
    unsubscribe = qtc.pyqtSignal(qtc.QObject)
    reset = qtc.pyqtSignal()
    additional_media_changed = qtc.pyqtSignal(list)
    loaded = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replay_widgets = []

        self.STATE = MediaState.AVAILABLE
        self._open_loading_tasks = 0

        self.grid = qtw.QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 10)
        self.MAX_WIDGETS = 4

        self.init_timer()

        self.vbox = qtw.QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.grid.addLayout(self.vbox, 0, 1)

        self._dead_widgets = []
        self._widget_2_path = {}

    @qtc.pyqtSlot(str, list)
    def load(self, file, additional_media=[]):
        if self.STATE == MediaState.AVAILABLE:
            self.STATE = MediaState.LOADING
            self._load(file, additional_media)
        else:
            logging.warning("Media is already loading -> ignoring new loading")

    def _load(self, file, additional_media=[]):
        self.pause()
        self.clear(notify=False)
        self.reset.emit()

        assert (
            self._open_loading_tasks == 0
        ), f"Open loading tasks must be 0 but is {self._open_loading_tasks}"
        assert (
            len(self.replay_widgets) == 0
        ), f"Replay widgets must be 0 but is {len(self.replay_widgets)}"
        assert (
            self.STATE == MediaState.LOADING
        ), f"State must be LOADING but is {self.STATE}"

        self._open_loading_tasks = 1 + len(additional_media)

        self.add_replay_widget(file, is_main_widget=True, from_load=True)
        for path in additional_media:
            self.add_replay_widget(path, from_load=True)

    def clear(self, notify=True):
        while self.replay_widgets:
            self.remove_replay_source(self.replay_widgets[0], notify)

    def add_replay_widget(self, path, is_main_widget=False, from_load=False):
        if self.STATE == MediaState.LOADING and not from_load:
            logging.warning("Media is loading -> ignoring new replay widget")
            return
        if len(self.replay_widgets) < self.MAX_WIDGETS:
            # is_main_widget = len(self.replay_widgets) == 0

            # select correct media_player

            media_type = media_type_of(path)
            if media_type == "video":
                widget = VideoPlayer(is_main_widget, self)
            elif media_type == "mocap":
                widget = MocapPlayer(is_main_widget, self)
            else:
                raise NotImplementedError(f"Media type {media_type} is not supported")

            if widget.is_main_replay_widget:
                self.grid.addWidget(widget, 0, 0)
            else:
                widget.remove_wanted.connect(self.remove_replay_source)
                self.vbox.addWidget(widget)

            if not widget.is_main_replay_widget:
                self._widget_2_path[id(widget)] = path

            widget.loaded.connect(self.widget_loaded)
            widget.failed.connect(self.widget_failed)
            widget.load(path)

    def _check_loading_finished(self):
        if self.STATE == MediaState.LOADING:
            self._open_loading_tasks -= 1
            if self._open_loading_tasks == 0:
                self.STATE = MediaState.AVAILABLE
                self.loaded.emit()
            assert (
                self._open_loading_tasks >= 0
            ), f"Open loading tasks must be >= 0 but is {self._open_loading_tasks}"
        else:
            assert (
                self._open_loading_tasks == 0
            ), f"Open loading tasks must be 0 but is {self._open_loading_tasks}"

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_loaded(self, widget: AbstractMediaPlayer):
        # check if widget belongs to current loading process

        widget.new_input_wanted.connect(self.add_replay_widget)
        widget.finished.connect(self.widget_terminated)
        self.replay_widgets.append(widget)
        proxy = MediaProxy(widget)

        self.subscribe.emit(proxy)

        if not widget.is_main_replay_widget and self.STATE != MediaState.LOADING:
            self.additional_media_changed.emit(self._widget_2_path.values())

        self._check_loading_finished()  # check if loading is finished

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_failed(self, widget):
        self.remove_replay_source(widget, ignore_errors=True)
        logging.error(f"COULD NOT LOAD {widget = }")

        self._check_loading_finished()  # check if loading is finished

        raise RuntimeError

    def remove_replay_source(self, widget, notify=True, ignore_errors=False):
        self.grid.removeWidget(widget)
        self.vbox.removeWidget(widget)
        proxy = media_proxy_map.get(id(widget))
        if proxy:
            self.unsubscribe.emit(proxy)
            del media_proxy_map[id(widget)]
        else:
            if not ignore_errors:
                logging.error(f"Could not find proxy for widget {widget}")
        if widget in self.replay_widgets:
            self.replay_widgets.remove(widget)
        else:
            if not ignore_errors:
                logging.error(f"Could not find widget {widget} in replay_widgets")
        widget.shutdown()

        if not widget.terminated:
            self._dead_widgets.append(
                widget
            )  # keep reference to widget until it is terminated

        if not widget.is_main_replay_widget:
            del self._widget_2_path[id(widget)]
            if notify:
                self.additional_media_changed.emit(self._widget_2_path.values())
            logging.debug(f"self._widget_2_path {self._widget_2_path}")

    def widget_terminated(self, widget):
        if widget in self._dead_widgets:
            self._dead_widgets.remove(widget)
        assert widget not in self.replay_widgets
        assert widget not in self._dead_widgets
        assert widget not in media_proxy_map.values()

    @qtc.pyqtSlot()
    def play(self):
        self.setPaused.emit(False)

    @qtc.pyqtSlot()
    def pause(self):
        self.setPaused.emit(True)

    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self.shutdown()
        return super().closeEvent(a0)

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        self.query_position_update.emit(pos)

    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.replay_speed_changed.emit(x)

    def on_timeout(self, pos):
        self.timeout.emit(pos)

    def init_timer(self):
        self.timer_thread = qtc.QThread()
        self.timer_worker = Synchronizer()
        self.timer_worker.moveToThread(self.timer_thread)

        # connecting worker and thread
        self.timer_worker.finished.connect(self.timer_thread.quit)
        self.timer_worker.finished.connect(self.timer_worker.deleteLater)
        self.timer_thread.finished.connect(self.timer_thread.deleteLater)

        # connecting signals and slots
        self.setPaused.connect(self.timer_worker.set_paused)
        self.stop.connect(self.timer_worker.stop)
        self.reset.connect(self.timer_worker.reset)
        self.replay_speed_changed.connect(self.timer_worker.set_replay_speed)
        self.subscribe.connect(self.timer_worker.subscribe)
        self.unsubscribe.connect(self.timer_worker.unsubscribe)
        self.query_position_update.connect(self.timer_worker.set_position)
        self.timer_worker.timeout.connect(self.on_timeout)

        self.timer_thread.start()

    def shutdown(self):
        self.clear(notify=False)
        self.stop.emit()
        self.timer_thread.quit()
        self.timer_thread.wait()

        logging.debug("Waiting for dead widgets to terminate")
        # wait for all widgets to be deleted

        for w in self._dead_widgets:
            w.kill()

        logging.info("Shut down MediaController successfully")

    @qtc.pyqtSlot()
    def settings_changed(self):
        for widget in self.replay_widgets:
            proxy = media_proxy_map.get(id(widget))
            if proxy is None:
                raise RuntimeError(f"Could not find proxy for widget {widget}")
            if proxy.fps != widget.fps:
                proxy.fps = widget.fps
                self.unsubscribe.emit(proxy)
                self.subscribe.emit(proxy)
