import logging
from logging.config import listen
from tkinter import Widget

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import functools

from .video import VideoPlayer
from .mocap_visualizer import MocapPlayer 

class Timer():
    def __init__(self) -> None:
        self.timer = qtc.QTimer()
        self.timer.setTimerType(qtc.Qt.PreciseTimer)
        self.interval = 5
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.timeout_handler)
        
        self.replay_speed = 1
    
        self.ms_counter = 0
        self.subscribers = []
        
    def timeout_handler(self) -> None:
        self.ms_counter += max(1, int(self.interval * self.replay_speed))
        for idx, (listener, cnt) in enumerate(self.subscribers):
            old_cnt = cnt
            r = 1000 / (listener.fps)
            new_cnt = int(self.ms_counter / r)
            self.subscribers[idx][1] = new_cnt
            for _ in range(new_cnt - old_cnt):
                listener.on_timeout()
    
    def subscribe(self, listener):
        r = 1000 / (listener.fps)
        cnt = int(self.ms_counter / r)
        self.subscribers.append([listener, int(cnt)])
        
    def unsubscribe(self, listener):
        for idx in range(len(self.subscribers)):
            if self.subscribers[idx][0] == listener:
                break
        else:
            return
        del self.subscribers[idx]
    
    def set_replay_speed(self, x):
        self.replay_speed = max(.01, x)
            
    def start(self):
        self.ms_counter = 0
        for idx in range(len(self.subscribers)):
            self.subscribers[idx][1] = 0
            
        self.timer.start()
        
    def stop(self):
        self.timer.stop()

    
class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(QMediaMainController, self).__init__(*args, **kwargs)
        self.replay_widgets = []
        self.grid = qtw.QGridLayout(self)
        self.next_row_idx = 0
        self.max_widgets = 4
        
        self.vbox = qtw.QVBoxLayout()
        self.grid.addLayout(self.vbox, 0, 1)
        
        self.timer = Timer()

    @qtc.pyqtSlot(str)
    def load_annotation(self, annotation):
        self.clear()
        self.add_replay_widget(annotation.input_file)   
      
    def clear(self):
        if self.replay_widgets:
            self.grid.removeWidget(self.replay_widgets[0])
            for w in self.replay_widgets[1:]:
                self.vbox.removeWidget(w)
            self.replay_widgets = []
                      
    def add_replay_widget(self, path):
        if len(self.replay_widgets) < self.max_widgets:
            file_ext = path.split('.')[-1]
            if file_ext in ['mp4', 'avi']:
                widget = VideoPlayer(self)
                
            if file_ext in ['csv']:
                # TODO CHECK IF .csv file actually holds mocap data!W
                try:
                    widget = MocapPlayer(self)
                except:
                    raise RuntimeError
            
            widget.load(path)
                        
            if not self.replay_widgets:
                # its going to be the main replay widget
                widget.set_main_replay_widget(True)
                widget.position_changed.connect(self.position_changed)
                self.grid.addWidget(widget, 0, 0)
            else:
                widget.set_main_replay_widget(False)
                widget.remove_wanted.connect(self.remove_replay_source)
                self.vbox.addWidget(widget)
                self.next_row_idx += 1
                widget.set_position(self.replay_widgets[0].position)
            
            widget.new_input_wanted.connect(self.add_replay_widget)
            self.replay_widgets.append(widget)
            self.timer.subscribe(widget)
          
    def remove_replay_source(self, widget):
        self.replay_widgets.remove(widget)
        self.grid.removeWidget(widget)
        self.timer.unsubscribe(widget)

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        for x in self.replay_widgets:
            x.set_position(pos)
        
    @qtc.pyqtSlot()
    def play(self):
        self.timer.start()
    
    @qtc.pyqtSlot()
    def pause(self):
        self.timer.stop()

    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.timer.set_replay_speed(x)
    
