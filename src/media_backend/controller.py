import logging
import time

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from ..data_classes.singletons import Settings

from .type_specific_player.video import VideoPlayer
from .type_specific_player.mocap import MocapPlayer 
from .player import AbstractMediaPlayer
from .timer import Timer


class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    query_position_update = qtc.pyqtSignal(int)
    setPaused = qtc.pyqtSignal(bool)
    stop = qtc.pyqtSignal()
    replay_speed_changed = qtc.pyqtSignal(float)
    subscribe = qtc.pyqtSignal(qtw.QWidget)
    unsubscribe = qtc.pyqtSignal(qtw.QWidget)
    reset = qtc.pyqtSignal()
    start_loop = qtc.pyqtSignal(int, int)
    end_loop = qtc.pyqtSignal()
    
    cleaned_up = qtc.pyqtSignal()
        
    def __init__(self, *args, **kwargs):
        super(QMediaMainController, self).__init__(*args, **kwargs)
        self.replay_widgets = []
        
        self.grid = qtw.QGridLayout(self)
        self.grid.setContentsMargins(0,0,0,10)
        self.MAX_WIDGETS = 4   
        
        self.init_timer()
        
        self.vbox = qtw.QVBoxLayout()
        self.vbox.setContentsMargins(0,0,0,0)
        self.grid.addLayout(self.vbox, 0, 1)
              
    @qtc.pyqtSlot(str)
    def load_annotation(self, annotation):
        self.pause()
        self.reset.emit()
        self.clear()
        self.add_replay_widget(annotation.input_file)
      
    def clear(self):
        if self.replay_widgets:
            main_widget = (self.replay_widgets[0])
            main_widget.shutdown()
            self.grid.removeWidget(main_widget)
            
            for w in self.replay_widgets[1:]:
                w.shutdown()
                self.vbox.removeWidget(w)
            self.replay_widgets = []
    
    # TODO VIDEO NEEDS TO BE ADDED           
    def add_replay_widget(self, path):
        if len(self.replay_widgets) < self.MAX_WIDGETS:
            file_ext = path.split('.')[-1]
            is_main_widget = len(self.replay_widgets) == 0
            
            if file_ext in ['mp4', 'avi']:
                widget = VideoPlayer(is_main_widget, self)
            
            if file_ext in ['csv']:
                # TODO CHECK IF .csv file actually holds mocap data!W
                try:
                    widget = MocapPlayer(is_main_widget, self)
                except:
                    raise RuntimeError
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
        self.start_loop.connect(widget.start_loop)
        self.end_loop.connect(widget.end_loop)
        
        if self.replay_widgets and self.replay_widgets[0].is_looping:
            start = self.replay_widgets[0].lower_bound
            end = self.replay_widgets[0].upper_bound
            widget.start_loop(start, end)
            
        self.replay_widgets.append(widget)
        logging.info('WIDGET LOADED')
        self.subscribe.emit(widget)

    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_failed(self, widget):
        self.remove_replay_source(widget)
        logging.error(f'COULD NOT LOAD {widget = }')
        raise RuntimeError
        
    def remove_replay_source(self, widget):
        widget.shutdown()
        self.replay_widgets.remove(widget)
        self.grid.removeWidget(widget)
        self.vbox.removeWidget(widget)
        self.unsubscribe.emit(widget)

    @qtc.pyqtSlot()
    def play(self):
        self.setPaused.emit(False)
    
    @qtc.pyqtSlot()
    def pause(self):
        self.setPaused.emit(True)
    
    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        logging.info('closeEvent called')
        self.shutdown()
        return super().closeEvent(a0)
    
    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        self.query_position_update.emit(pos)
    
    @qtc.pyqtSlot(float)    
    def set_replay_speed(self, x):
        self.replay_speed_changed.emit(x)
    
    @qtc.pyqtSlot(int, int)
    def start_loop_slot(self, x, y):
        self.start_loop.emit(x,y)
    
    @qtc.pyqtSlot()
    def end_loop_slot(self):
        self.end_loop.emit()
        
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
        logging.info('Shut down MediaController successfully')
    
    @qtc.pyqtSlot()
    def settings_changed(self):
        settings = Settings.instance()
        for widget in self.replay_widgets:
            if isinstance(widget, MocapPlayer):
                if widget.fps != settings.refresh_rate:
                    # reloading mocap_widget with new refresh rate
                    logging.info(f'RESETTING {widget = }')
                    self.unsubscribe.emit(widget)
                    widget.fps = settings.refresh_rate
                    self.subscribe.emit(widget)
    