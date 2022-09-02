import logging
from re import S
import time

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from ..data_classes.singletons import Settings

from .video import VideoPlayer
from .mocap_visualizer import MocapPlayer 
from .media_player import AbstractMediaPlayer

class FairQueue():
    def __init__(self) -> None:
        self.items = []
        self.count = 0
        
    def push(self, item : AbstractMediaPlayer):
        assert isinstance(item, AbstractMediaPlayer)
        for idx, (elem_2, _) in enumerate(self.items):
            if item == elem_2:
                self._increase_item(idx)
                break
        else:
            self.append_new_item(item)
        # print(self.items)
    
    def append_new_item(self, item):
        self.items.append([item, 1])
        self.count += 1
    
    def _pop_item(self, idx):
        elem, _ = self.items[idx]
        
        # decreasing item
        self.items[idx][1] -= 1
        self.count -= 1
        
        # deleting if item empty
        if self.items[idx][1] == 0:
            del self.items[idx]
        
        return elem
    
    def _increase_item(self, idx):
        self.items[idx][1] += 1
        self.count += 1
    
    def pop(self):
        if self.has_elements():
            max_idx = 0
            max_ratio = 0
            
            for idx, (elem, count) in enumerate(self.items):
                fps = elem.fps
                ratio = count / fps # the higher the ratio, the earlier the update is required     
                if ratio > max_ratio:
                    max_idx = idx
                    max_ratio = ratio
                        
            # pop element with highest ratio, and return it
            return self._pop_item(max_idx)            
        else:
            return None
        
    def has_elements(self):
        return self.count > 0
    
    def remove_item(self, item):
        for idx, (it, _) in enumerate(self.items):
            if item == it:
                self.count -= self.items[idx][1]
                del self.items[idx]
                break
            
    def _check_consistency(self):
        # Check: sum of counts = self.count
        # Check: No duplicated items
        # Check: Efficiency (?)    
        pass
            
    def clear(self):
        self.items = []
        self.count = 0
    
    def __len__(self):
        return self.count
    
    
class Timer(qtc.QObject):
    new_task = qtc.pyqtSignal(qtw.QWidget)
    finished = qtc.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.queue = FairQueue()
        self.currently_updating = []
        
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
                self.queue.clear()
                time.sleep(self.PASSIVE_IDLE_TIME)
                self.last_real_time_ms = time_in_millis()
                continue
            
            self.update_alpha()
            self.compute_time()
            self.update_queue()
            
            logging.info('ALPHA = {} | QUEUE_SIZE = {} '.format(self.alpha, len(self.queue)))
            
            free = len(self.currently_updating) < self.MAX_OPEN_TASKS
            if free and self.queue.has_elements():
                self.process_queue()
            else:
                time.sleep(self.ACTIVE_IDLE_TIME)
        logging.info('*** Timer FINISHED ***')
        self.finished.emit()
        
    def setPaused(self, x):
        self.pause = bool(x)
            
    def update_queue(self):
        for idx, (listener, cnt) in enumerate(self.subscribers):
            old_cnt = cnt
            r = 1000 / (listener.fps)
            new_cnt = int(self.time / r)
            self.subscribers[idx][1] = new_cnt
            for _ in range(new_cnt - old_cnt):
                self.queue.push(listener)
    
    def process_queue(self):
        if self.queue.has_elements():
            listener = self.queue.pop()
            self.currently_updating.append(listener)
            self.new_task.emit(listener)
            logging.info('CURRENTLY_UPDATING = {}'.format(len(self.currently_updating)))
           
    @qtc.pyqtSlot(qtw.QWidget)
    def confirm_task(self, listener):
        for idx, l in enumerate(self.currently_updating):
            if listener == l:
                del self.currently_updating[idx]
                break
            
    def update_alpha(self):
        n = len(self.queue)
        self.alpha = (100 - n) / 100
        
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
            # listener not found!
            raise RuntimeError
        del self.subscribers[idx]
        self.queue.remove_item(listener)
       
    def reset(self):
        self.queue = FairQueue()
        self.currently_updating = []
        self.subscribers = []
        self.time = 0
        self.last_real_time_ms = time_in_millis()
    
    def set_replay_speed(self, x):
        self.replay_speed = max(.01, x)
    

class TaskScheduler(qtc.QObject):
    task_finished = qtc.pyqtSignal(qtw.QWidget)
    finished = qtc.pyqtSignal()
    
    def __init__(self) -> None:
        super().__init__()
        self.active = False
        
        self.open_timeouts = []
        
        self.next_position = None
        self.widgets = None
               
    def run(self):
        self.active = True
        
        print(self.widgets, self.next_position)
        
        while self.active:
            if self.next_position and self.widgets:
                self.change_position()
                continue
            if self.open_timeouts:
                self.process_timeout()
            time.sleep(0.005)
        logging.info('*** TaskScheduler FINISHED ***')
        self.finished.emit()
    
    def process_timeout(self):
        # logging.info('solving timeout')
        listener = self.open_timeouts.pop(0)
        listener.on_timeout()
        self.task_finished.emit(listener)
        
    @qtc.pyqtSlot(qtw.QWidget)
    def add_timeout_for(self, widget):
        # logging.info('ADDING TIMEOUT')
        self.open_timeouts.append(widget)
    
    @qtc.pyqtSlot(qtw.QWidget, int)
    def set_position(self, widgets, pos):
        # logging.info('setting new position')
        self.next_position = pos
        self.widgets = widgets
        
        if not self.active:
            self.change_position()
        
    def change_position(self):
        # logging.info('changing position')
        widgets, pos = self.widgets, self.next_position
        self.widgets, self.next_position = None, None
        
        if widgets:
            main_widget = widgets[0]
            main_widget.set_position(pos)
            for w in widgets[1:]:
                synchronize(w, main_widget)
    
    def stop(self):
        self.active = False


class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    widget_pos_update = qtc.pyqtSignal(qtw.QWidget, int)
    

    def __init__(self, *args, **kwargs):
        super(QMediaMainController, self).__init__(*args, **kwargs)
        self.replay_widgets = []
        self.grid = qtw.QGridLayout(self)
        self.MAX_WIDGETS = 4

        self.replay_speed = 1        
        
        self.vbox = qtw.QVBoxLayout()
        self.grid.addLayout(self.vbox, 0, 1)
        
        self.init_workers()
        

    @qtc.pyqtSlot(str)
    def load_annotation(self, annotation):
        self.pause()
        self.clear()
        self.timer_worker.reset()
        self.add_replay_widget(annotation.input_file)
      
    def clear(self):
        if self.replay_widgets:
            self.grid.removeWidget(self.replay_widgets[0])
            for w in self.replay_widgets[1:]:
                self.vbox.removeWidget(w)
            self.replay_widgets = []
                      
    def add_replay_widget(self, path):
        if len(self.replay_widgets) < self.MAX_WIDGETS:
            file_ext = path.split('.')[-1]
            if file_ext in ['mp4', 'avi']:
                widget = VideoPlayer(self)
                
            if file_ext in ['csv']:
                # TODO CHECK IF .csv file actually holds mocap data!W
                try:
                    widget = MocapPlayer(self)
                except:
                    raise RuntimeError
                        
            if not self.replay_widgets:
                # its going to be the main replay widget
                widget.set_main_replay_widget(True)
                widget.position_changed.connect(self.position_changed)
                self.grid.addWidget(widget, 0, 0)
            else:
                widget.set_main_replay_widget(False)
                widget.remove_wanted.connect(self.remove_replay_source)
                self.vbox.addWidget(widget)
            
            widget.new_input_wanted.connect(self.add_replay_widget)

            widget.loaded.connect(self.widget_loaded)
            widget.failed.connect(self.widget_failed)
            widget.load(path)
    
    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_loaded(self, widget):
        self.replay_widgets.append(widget)
        if len(self.replay_widgets) > 1:
            synchronize(widget, self.replay_widgets[0])
        self.timer_worker.subscribe(widget)
        
    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_failed(self, widget):
        self.remove_replay_source(widget)
        
    def remove_replay_source(self, widget):
        self.replay_widgets.remove(widget)
        self.grid.removeWidget(widget)
        self.timer_worker.unsubscribe(widget)
        widget.setParent(None)
        del widget

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        if self.scheduler_worker:
            self.scheduler_worker.set_position(self.replay_widgets, pos)
        else:
            self.init_workers()
            self.scheduler_worker.set_position(self.replay_widgets, pos)
         
    @qtc.pyqtSlot()
    def play(self):
        self.start_threads()
        self.timer_worker.setPaused(False)
        
    @qtc.pyqtSlot()
    def pause(self):
        self.stop_threads()
        
        if self.replay_widgets:
            self.scheduler_worker.set_position(self.replay_widgets, self.replay_widgets[0].position)
    
    def init_workers(self):
        self.timer_thread = qtc.QThread()
        self.scheduler_thread = qtc.QThread()
        
        # TIMER
        self.timer_worker = Timer()
        self.scheduler_worker = TaskScheduler()
        
        self.timer_worker.moveToThread(self.timer_thread)      
        
        self.timer_thread.started.connect(self.timer_worker.run)
        self.timer_worker.finished.connect(self.timer_thread.quit)
        self.timer_worker.finished.connect(self.timer_worker.deleteLater)
        self.timer_thread.finished.connect(self.timer_thread.deleteLater)
        
        # SCHEDULER        
        self.scheduler_worker.moveToThread(self.scheduler_thread)
        
        self.scheduler_thread.started.connect(self.scheduler_worker.run)
        self.scheduler_worker.finished.connect(self.scheduler_thread.quit)
        self.scheduler_worker.finished.connect(self.scheduler_worker.deleteLater)
        self.scheduler_worker.finished.connect(self.scheduler_thread.deleteLater)
        
        # Inter-Thread connections
        # self.timer_worker.new_task.connect(self.scheduler_worker.add_timeout_for)
        # self.scheduler_worker.task_finished.connect(self.timer_worker.confirm_task)
        
        self.timer_worker.new_task.connect(self.on_timeout)
        self.scheduler_worker.task_finished.connect(self.confirm_task)
    
    def stop_threads(self):
        old_timer = self.timer_worker
        old_timer_thread = self.timer_thread
        old_scheduler = self.scheduler_worker
        old_scheduler_thread = self.scheduler_thread
        
        old_timer.stop()
        old_scheduler.stop()
        
        old_timer_thread.quit()
        old_scheduler_thread.quit()
        
        #old_timer_thread.wait()
        #old_scheduler_thread.wait()
        
        # self.init_workers()
    
        logging.info('All threads stopped!')
        
    def start_threads(self):
        self.init_workers()
        
        # Init timer
        self.timer_worker.set_replay_speed(self.replay_speed)
        for w in self.replay_widgets:
            self.timer_worker.subscribe(w)               
        
        self.timer_thread.start()
        self.scheduler_thread.start()
                   
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.replay_speed = x
        self.timer_worker.set_replay_speed(x)
    
    @qtc.pyqtSlot()
    def settings_changed(self):
        settings = Settings.instance()
        show_mocap_grid = settings.mocap_grid
        use_dynamic_mocap_grid = settings.mocap_grid_dynamic
        for widget in self.replay_widgets:
            if isinstance(widget, MocapPlayer):
                widget.set_floor_grid(show_mocap_grid, use_dynamic_mocap_grid)
                if widget.fps != settings.refresh_rate:
                    # reloading mocap_widget with new refresh rate
                    self.timer_worker.unsubscribe(widget)
                    widget.fps = settings.refresh_rate
                    synchronize(widget, self.replay_widgets[0])                    
                    self.timer_worker.subscribe(widget)
    
    @qtc.pyqtSlot(qtw.QWidget)
    def on_timeout(self, widget):
        self.scheduler_worker.add_timeout_for(widget)
    
    @qtc.pyqtSlot(qtw.QWidget)
    def confirm_task(self, widget):
        self.timer_worker.confirm_task(widget)
        

def sleep_(duration, get_now=time.perf_counter):
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now() 
    
    
def time_in_millis():
    t = time.time()
    return int(t * 1000)
    
def synchronize(to_sync, sync_with):
    if to_sync != sync_with:
        pos = sync_with.position
        
        if to_sync.fps != sync_with.fps:
            frame_rate_ratio =  to_sync.fps / sync_with.fps
            pos_adjusted = int(frame_rate_ratio * pos)
            to_sync.set_position(pos_adjusted)
        else:
            to_sync.set_position(pos)
