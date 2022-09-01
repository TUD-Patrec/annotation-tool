import logging

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from ..data_classes.singletons import Settings

from .video import VideoPlayer
from .mocap_visualizer import MocapPlayer 
import time 
  
class TimerThread(qtc.QThread):
    new_task = qtc.pyqtSignal(qtw.QWidget)
    def __init__(self):
        super().__init__()
        self.queue = []
        self.currently_updating = None
        
        # Constants
        self.MAX_OPEN_TASKS = 10
        self.PASSIVE_IDLE_TIME = 0.2
        self.ACTIVE_IDLE_TIME = 0.005
        
        self.subscribers = []
        self.active = True
        self.pause = True
        
        self.alpha = 1
        self.replay_speed = 1
        
        self.time = 0
        self.last_real_time_ms = None
        
    def compute_time(self):
        current = time_in_millis()
        time_multiplier = self.replay_speed * self.alpha
        delta = int(time_multiplier * (current - self.last_real_time_ms))
        if delta > 0:
            self.time += delta
            self.last_real_time_ms = current
    
    def run(self):
        self.last_real_time_ms = time_in_millis()
        
        while self.active:            
            if self.pause or len(self.subscribers) == 0:
                self.queue = []
                time.sleep(self.PASSIVE_IDLE_TIME)
                self.last_real_time_ms = time_in_millis()
                continue
            
            self.update_alpha()
            self.compute_time()
            self.update_queue()
            
            logging.info('ALPHA = {} | QUEUE_SIZE = {}'.format(self.alpha, len(self.queue)))
            
            free = self.currently_updating is None
            if free and self.queue:
                self.process_queue()
            else:
                time.sleep(self.ACTIVE_IDLE_TIME)
        logging.info('*** THREAD FINISHED ***')
        
    def setPaused(self, x):
        self.pause = bool(x)
         
    def update_queue(self):
        for idx, (listener, cnt) in enumerate(self.subscribers):
            old_cnt = cnt
            r = 1000 / (listener.fps)
            new_cnt = int(self.time / r)
            self.subscribers[idx][1] = new_cnt
            for _ in range(new_cnt - old_cnt):
                self.queue.append([listener, True])
    
    def process_queue(self):
        while self.queue:
            listener, ok = self.queue.pop(0)
            if ok:
                self.currently_updating = listener     
                self.new_task.emit(listener)
                break
        else:
            self.locked = None
            
    @qtc.pyqtSlot()
    def confirm_task(self):
        self.currently_updating = None
            
    def update_alpha(self):
        n = len(self.queue)
        self.alpha = max(0.01, (100 - n) / 100)
        
    def stop(self):
        self.active = False
    
    def subscribe(self, listener):
        r = 1000 / listener.fps
        cnt = self.time / r
        self.subscribers.append([listener, int(cnt)])
        
    def unsubscribe(self, listener):
        for idx in range(len(self.subscribers)):
            if self.subscribers[idx][0] == listener:
                break
        else:
            return
        del self.subscribers[idx]
        for idx in range(len(self.queue)):
            if self.queue[idx][0] == listener:
                self.queue[idx][1] = False
        if self.currently_updating == listener:
            self.currently_updating = None

    def reset(self):
        self.queue = []
        self.currently_updating = None
        self.subscribers = []
        self.time = 0
        self.last_real_time_ms = time_in_millis()
    
    def set_replay_speed(self, x):
        self.replay_speed = max(.01, x)
    

class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    widget_pos_update = qtc.pyqtSignal(qtw.QWidget, int)
    task_finished = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QMediaMainController, self).__init__(*args, **kwargs)
        self.replay_widgets = []
        self.grid = qtw.QGridLayout(self)
        self.next_row_idx = 0
        self.max_widgets = 4
        
        self.vbox = qtw.QVBoxLayout()
        self.grid.addLayout(self.vbox, 0, 1)
        
        self.make_new_timer(1)

    @qtc.pyqtSlot(str)
    def load_annotation(self, annotation):
        self.pause()
        self.clear()
        self.timer.reset()
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
                self.sync_with_main(widget)
                
            
            widget.new_input_wanted.connect(self.add_replay_widget)
            self.replay_widgets.append(widget)
            self.timer.subscribe(widget)
            
          
    def remove_replay_source(self, widget):
        print('REMOVING', widget)
        self.replay_widgets.remove(widget)
        self.grid.removeWidget(widget)
        self.timer.unsubscribe(widget)
        widget.setParent(None)

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        if self.replay_widgets:
            self.replay_widgets[0].set_position(pos)
            for w in self.replay_widgets[1:]:
                self.sync_with_main(w)
        #for idx, w in enumerate(self.replay_widgets):
        #    logging.info('IDX: {} | Position = {}'.format(idx, w.get_timestamp()))
        pass
    
    def sync_with_main(self, x):
        main_fps = self.replay_widgets[0].fps
        pos = self.replay_widgets[0].position
        
        if x.fps != main_fps:
            pos_adjusted = int(pos * x.fps / main_fps)
            x.set_position(pos_adjusted)
        else:
            x.set_position(pos)
         
    @qtc.pyqtSlot()
    def play(self):
        self.timer.setPaused(False)
    
    @qtc.pyqtSlot()
    def pause(self):
        self.timer.setPaused(True)
        for w in self.replay_widgets:
            self.sync_with_main(w)
        
    def make_new_timer(self, replay_speed):
        self.timer = TimerThread()
        self.timer.set_replay_speed(replay_speed)
        
        self.timer.new_task.connect(self.on_timeout)
        self.task_finished.connect(self.timer.confirm_task)
        
        for w in self.replay_widgets:
            self.timer.subscribe(w)
        self.timer.start()
         
    @qtc.pyqtSlot(qtw.QWidget)
    def on_timeout(self, widget):
        widget.on_timeout()
        self.task_finished.emit()
           
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.timer.set_replay_speed(x)
    
    @qtc.pyqtSlot()
    def settings_changed(self):
        settings = Settings.instance()
        show_mocap_grid = settings.mocap_grid
        use_dynamic_mocap_grid = settings.mocap_grid_dynamic
        for widget in self.replay_widgets:
            if isinstance(widget, MocapPlayer):
                widget.set_floor_grid(show_mocap_grid, use_dynamic_mocap_grid)
        

def sleep_(duration, get_now=time.perf_counter):
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now() 
    
    
def time_in_millis():
    t = time.time()
    return int(t * 1000)
    
