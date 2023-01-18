import logging

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from src.media.backend.player import AbstractMediaPlayer
from src.media.backend.timer import Timer
from src.media.backend.type_specific_player.mocap import MocapPlayer
from src.media.backend.type_specific_player.video import VideoPlayer
from src.media.media_types import MediaType, media_type_of
from src.settings import settings

media_proxy_map = {}


class MediaProxy(qtc.QObject):
    ACK_timeout: qtc.pyqtSignal = qtc.pyqtSignal(qtc.QObject)
    ACK_setpos: qtc.pyqtSignal = qtc.pyqtSignal(qtc.QObject)
    set_position = qtc.pyqtSignal(int)
    timeout = qtc.pyqtSignal()

    def __init__(self, media_widget: AbstractMediaPlayer):
        super().__init__()
        self.id = id(media_widget)
        self.fps = media_widget.fps
        self.position = media_widget.position

        media_proxy_map[id(media_widget)] = (self, media_widget)

        media_widget.ACK_timeout.connect(self.forward_ACK_timeout)
        media_widget.ACK_setpos.connect(self.forward_ACK_setpos)
        self.timeout.connect(media_widget.on_timeout)
        self.set_position.connect(media_widget.set_position)

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
        self.position = self.media_widget.position
        self.ACK_timeout.emit(self)

    @qtc.pyqtSlot()
    def forward_ACK_setpos(self):
        self.position = self.media_widget.position
        self.ACK_setpos.emit(self)

    @property
    def media_widget(self):
        return media_proxy_map[self.id][1]


class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    query_position_update = qtc.pyqtSignal(int)
    setPaused = qtc.pyqtSignal(bool)
    stop = qtc.pyqtSignal()
    replay_speed_changed = qtc.pyqtSignal(float)
    subscribe = qtc.pyqtSignal(qtc.QObject)
    unsubscribe = qtc.pyqtSignal(qtc.QObject)
    reset = qtc.pyqtSignal()

    cleaned_up = qtc.pyqtSignal()

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

    @qtc.pyqtSlot(str)
    def load(self, file):
        self.pause()
        self.reset.emit()
        self.clear()
        self.add_replay_widget(file)

    def clear(self):
        if self.replay_widgets:
            main_widget = self.replay_widgets[0]
            main_widget.shutdown()
            self.grid.removeWidget(main_widget)

            for w in self.replay_widgets[1:]:
                w.shutdown()
                self.vbox.removeWidget(w)
            self.replay_widgets = []

    def add_replay_widget(self, path):
        if len(self.replay_widgets) < self.MAX_WIDGETS:
            is_main_widget = len(self.replay_widgets) == 0

            # select correct media_player
            media_type = media_type_of(path)
            if media_type == MediaType.VIDEO:
                widget = VideoPlayer(is_main_widget, self)
            elif media_type == MediaType.MOCAP:
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

            widget.loaded.connect(self.widget_loaded)
            widget.failed.connect(self.widget_failed)
            widget.load(path)

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_loaded(self, widget: AbstractMediaPlayer):
        widget.new_input_wanted.connect(self.add_replay_widget)
        self.replay_widgets.append(widget)

        proxy = MediaProxy(widget)

        logging.info("WIDGET LOADED")
        self.subscribe.emit(proxy)
        logging.info("WIDGET SUBSCRIBED")

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_failed(self, widget):
        self.remove_replay_source(widget)
        logging.error(f"COULD NOT LOAD {widget = }")
        raise RuntimeError

    def remove_replay_source(self, widget):
        widget.shutdown()
        self.replay_widgets.remove(widget)
        self.grid.removeWidget(widget)
        self.vbox.removeWidget(widget)

        proxy = media_proxy_map.get(id(widget))[0]
        if proxy:
            self.unsubscribe.emit(proxy)
            del media_proxy_map[id(widget)]

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
        self.clear()
        self.stop.emit()
        self.timer_thread.quit()
        self.timer_thread.wait()
        self.cleaned_up.emit()
        logging.info("Shut down MediaController successfully")

    @qtc.pyqtSlot()
    def settings_changed(self):
        for widget in self.replay_widgets:
            if isinstance(widget, MocapPlayer):
                if widget.fps != settings.refresh_rate:
                    # reloading mocap_widget with new refresh rate
                    logging.info(f"RESETTING {widget = }")
                    self.unsubscribe.emit(widget)
                    widget.fps = settings.refresh_rate
                    self.subscribe.emit(widget)
