import logging
from typing import List, Tuple

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.media.backend.player import AbstractMediaPlayer
from annotation_tool.media.backend.timer import Timer
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
        media_widget.ACK_timeout.connect(self.forward_ACK_timeout)
        media_widget.ACK_setpos.connect(self.forward_ACK_setpos)
        self.timeout.connect(media_widget.on_timeout)
        self.set_position.connect(media_widget.set_position)

        media_proxy_map[id(media_widget)] = self
        self.media_widget = media_widget

        self.fps = media_widget.fps

    @qtc.pyqtSlot(qtc.QObject)
    def on_timeout_(self, proxy):
        if proxy is self:
            self.timeout.emit()

    @qtc.pyqtSlot(qtc.QObject, int)
    def set_position_(self, proxy, position):
        if proxy is self:
            self.set_position.emit(position)

    @qtc.pyqtSlot()
    def forward_ACK_timeout(self):
        self.ACK_timeout.emit(self)

    @qtc.pyqtSlot()
    def forward_ACK_setpos(self):
        self.ACK_setpos.emit(self)

    @property
    def position(self):
        return self.media_widget.position


class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
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

        self.grid = qtw.QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 10)
        self.MAX_WIDGETS = 4

        self.init_timer()

        self.vbox = qtw.QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.grid.addLayout(self.vbox, 0, 1)

        self._dead_widgets = []
        self._widget_2_path = {}

        self._loading_idx = 0  # keep track of how many times load() was called
        self._loading_widgets: List[Tuple[AbstractMediaPlayer, int]] = []

    @qtc.pyqtSlot(str)
    def load(self, file):
        self._loading_idx += 1
        self.pause()
        self.clear(notify=False)
        self.reset.emit()
        self.add_replay_widget(file)

    def clear(self, notify=True):
        while self.replay_widgets:
            self.remove_replay_source(self.replay_widgets[0], notify)

    def add_replay_widget(self, path):
        if len(self.replay_widgets) < self.MAX_WIDGETS:
            is_main_widget = len(self.replay_widgets) == 0

            # select correct media_player

            media_type = media_type_of(path)
            if media_type == "video":
                widget = VideoPlayer(is_main_widget, self)
            elif media_type == "mocap":
                widget = MocapPlayer(is_main_widget, self)
            else:
                raise NotImplementedError("Media type not supported")

            if widget.is_main_replay_widget:
                widget.position_changed.connect(self.position_changed)
                self.grid.addWidget(widget, 0, 0)
            else:
                widget._reference_fps = self.replay_widgets[0].fps
                widget._reference_N = self.replay_widgets[0].n_frames
                widget.remove_wanted.connect(self.remove_replay_source)
                self.vbox.addWidget(widget)

            if not widget.is_main_replay_widget:
                self._widget_2_path[id(widget)] = path

            widget.loaded.connect(self.widget_loaded)
            widget.failed.connect(self.widget_failed)
            self._loading_widgets.append(
                (widget, self._loading_idx)
            )  # keep track of which widget was loaded when
            widget.load(path)

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_loaded(self, widget: AbstractMediaPlayer):
        # remove widget from loading list
        for i, (w, idx) in enumerate(self._loading_widgets):
            if w is widget:
                _, idx_ = self._loading_widgets.pop(i)
                break
        else:
            raise RuntimeError("Widget was not in loading list")

        # check if widget belongs to current loading process
        if idx_ != self._loading_idx:
            self.remove_replay_source(widget, ignore_errors=True)
            logging.debug(
                f"Widget {widget} was loaded in a previous loading process. Ignoring it."
            )
            return

        widget.new_input_wanted.connect(self.add_replay_widget)
        widget.finished.connect(self.widget_terminated)
        self.replay_widgets.append(widget)
        proxy = MediaProxy(widget)

        if not widget.is_main_replay_widget:
            self.additional_media_changed.emit(self._widget_2_path.values())
        else:
            self.loaded.emit()
        self.subscribe.emit(proxy)

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_failed(self, widget):
        # remove widget from loading list
        for i, (w, idx) in enumerate(self._loading_widgets):
            if w is widget:
                _, idx_ = self._loading_widgets.pop(i)
                break
        else:
            raise RuntimeError("Widget was not in loading list")

        self.remove_replay_source(widget, ignore_errors=True)
        logging.error(f"COULD NOT LOAD {widget = }")
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

    def init_timer(self):
        self.timer_thread = qtc.QThread()
        self.timer_worker = Timer()
        self.timer_worker.moveToThread(self.timer_thread)

        # connecting worker and thread
        self.timer_thread.started.connect(self.timer_worker.run)
        self.timer_worker.finished.connect(self.timer_thread.quit)
        self.timer_worker.finished.connect(self.timer_worker.deleteLater)
        self.timer_thread.finished.connect(self.timer_thread.deleteLater)

        # connecting signals and slots
        self.setPaused.connect(self.timer_worker.setPaused)
        self.stop.connect(self.timer_worker.stop)
        self.reset.connect(self.timer_worker.reset)
        self.replay_speed_changed.connect(self.timer_worker.set_replay_speed)
        self.subscribe.connect(self.timer_worker.subscribe)
        self.unsubscribe.connect(self.timer_worker.unsubscribe)
        self.query_position_update.connect(self.timer_worker.query_position_update)

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
