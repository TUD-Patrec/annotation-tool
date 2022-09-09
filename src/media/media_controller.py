import logging
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
                
    def clear(self):
        self.items = []
        self.count = 0
    
    def __len__(self):
        return self.count
    

class Timer(qtc.QObject):
    finished = qtc.pyqtSignal()
    timeout_signal = qtc.pyqtSignal(qtw.QWidget)
    change_position_signal = qtc.pyqtSignal(int)
    sync_needed = qtc.pyqtSignal()
     
    def init(self):
        self.queue = FairQueue()
        self.next_position = None
        self.open_tasks = []
        
        self.queried_pos_updates = 0
        
        # Constants
        self.MAX_OPEN_TASKS = 10
        self.ACTIVE_IDLE_TIME = 0.005
        self.PASSIVE_IDLE_TIME = 0.05
        
        self.subscribers = []
        self.active = True
        self.paused = True
        self.sync_after_pause = False
        
        self.alpha = 1
        self.replay_speed = 1
        
        self.time = 0
        self.last_real_time_ms = None
        
        self.thread_ = self.thread()
     
    def compute_time(self):
        assert qtc.QThread.currentThread() is self.thread_
        current = time_in_millis()
        time_multiplier = self.replay_speed * self.alpha
        delta = int(time_multiplier * (current - self.last_real_time_ms))
        if delta > 0:
            self.time += delta
            self.last_real_time_ms = current
    
    def run(self):
        self.init()
        self.last_real_time_ms = time_in_millis()
                
        while self.active:
            assert qtc.QThread.currentThread() is self.thread_
            
            # Clearing the event
            qtc.QCoreApplication.processEvents()
            
            # Position update available - has priority over all other tasks
            if self.next_position:
                self.change_position()
                continue
                           
            elif self.paused or len(self.subscribers) == 0:
                self.queue.clear()
                if self.sync_after_pause:
                    self.sync_after_pause = False
                    self.sync_needed.emit()
                time.sleep(self.PASSIVE_IDLE_TIME)
                self.last_real_time_ms = time_in_millis()
                continue
            
            self.compute_time()
            self.update_queue()
            self.update_alpha()
            logging.info('ALPHA = {} | QUEUE_SIZE = {} | OPEN_TASKS_SIZE = {} '.format(self.alpha, len(self.queue), len(self.open_tasks)))
            
            if len(self.open_tasks) < self.MAX_OPEN_TASKS and self.queue.has_elements():
                self.process_queue()
            else:
                time.sleep(self.ACTIVE_IDLE_TIME)
            
        logging.info('*** Timer FINISHED ***')
        self.finished.emit()
          
    def update_queue(self):
        assert qtc.QThread.currentThread() is self.thread_
        for idx, (listener, cnt) in enumerate(self.subscribers):
            old_cnt = cnt
            r = 1000 / (listener.fps)
            new_cnt = int(self.time / r)
            self.subscribers[idx][1] = new_cnt
            for _ in range(new_cnt - old_cnt):
                self.queue.push(listener)
    
    def process_queue(self):
        assert qtc.QThread.currentThread() is self.thread_
        while len(self.open_tasks) < self.MAX_OPEN_TASKS and self.queue.has_elements():
            listener = self.queue.pop()
            self.open_tasks.append(listener)
            # logging.info(f'SENDING TIMEOUT FROM {qtc.QThread.currentThread() = }')
            self.timeout_signal.emit(listener)

    def update_alpha(self):
        assert qtc.QThread.currentThread() is self.thread_
        N = len(self.queue)
        THETA = len(self.subscribers) * 2
        if N < THETA:
            self.alpha = 1
        else:
            MAX_QUEUE_LEN = 25
            EPSILON = 0.001
            
            self.alpha = max(EPSILON, 1 - (N - THETA) / (MAX_QUEUE_LEN - THETA) )
            
    def change_position(self):
        assert qtc.QThread.currentThread() is self.thread_
        pos = self.next_position
        self.next_position = None
        # logging.debug(f'{self.queried_pos_updates = }')
        self.queried_pos_updates = 0
        # logging.info(f'SENDING POSITION UPDATE FROM {qtc.QThread.currentThread() = }')
        self.change_position_signal.emit(pos)
    
    @qtc.pyqtSlot(qtw.QWidget)    
    def confirm_task(self, t):
        assert qtc.QThread.currentThread() is self.thread_
        for idx, l in enumerate(self.open_tasks):
            if t == l:
                del self.open_tasks[idx]
                break     
    
    @qtc.pyqtSlot()    
    def stop(self):
        assert qtc.QThread.currentThread() is self.thread_
        logging.info('STOPPING TIMER')
        self.active = False
    
    @qtc.pyqtSlot(qtw.QWidget)
    def subscribe(self, listener):
        assert qtc.QThread.currentThread() is self.thread_
        r = 1000 / listener.fps
        cnt = self.time / r
        self.subscribers.append([listener, int(cnt)])
        
        # resetting
        self.sync_needed.emit()
        self.queue.clear()
        self.open_tasks = []
        self.time = 0
        self.last_real_time_ms = time_in_millis()
     
    @qtc.pyqtSlot(qtw.QWidget)
    def unsubscribe(self, listener):
        assert qtc.QThread.currentThread() is self.thread_
        for idx in range(len(self.subscribers)):
            if self.subscribers[idx][0] is listener:
                break
        else:
            raise RuntimeError
        del self.subscribers[idx]
        self.queue.remove_item(listener)
        # HACKY - reimplement later
        for _ in range(len(self.open_tasks)):
            self.confirm_task(listener)
    
    @qtc.pyqtSlot(bool)
    def setPaused(self, x):
        assert qtc.QThread.currentThread() is self.thread_
        # logging.info(f'PAUSE SIGNAL RECEIVED in {qtc.QThread.currentThread() = }')
        self.paused = bool(x)
        if self.paused:
            self.sync_after_pause = True
    
    @qtc.pyqtSlot()
    def reset(self):
        assert qtc.QThread.currentThread() is self.thread_
        self.queue.clear()
        self.open_tasks = []
        self.subscribers = []
        self.time = 0
        self.last_real_time_ms = time_in_millis()
        self.paused = True
    
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        assert qtc.QThread.currentThread() is self.thread_
        # logging.info('Signal received!')
        self.replay_speed = max(.01, x)

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        assert qtc.QThread.currentThread() is self.thread_
        self.next_position = pos
        self.queried_pos_updates += 1
        

class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    setPaused = qtc.pyqtSignal(bool)
    replay_speed_changed = qtc.pyqtSignal(float)
    subscribe = qtc.pyqtSignal(qtw.QWidget)
    unsubscribe = qtc.pyqtSignal(qtw.QWidget)
    reset = qtc.pyqtSignal()
    task_finished = qtc.pyqtSignal(qtw.QWidget)
    query_new_position = qtc.pyqtSignal(int)
    stop_signal = qtc.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(QMediaMainController, self).__init__(*args, **kwargs)
        self.replay_widgets = []
        self.grid = qtw.QGridLayout(self)
        self.MAX_WIDGETS = 4

        self.replay_speed = 1        
        
        self.init_timer()
        self.timer_thread.start()
        
        self.vbox = qtw.QVBoxLayout()
        self.grid.addLayout(self.vbox, 0, 1)
        
        self.thread_ = self.thread()
      
    @qtc.pyqtSlot(str)
    def load_annotation(self, annotation):
        self.pause()
        self.reset.emit()
        self.clear()
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
        self.subscribe.emit(widget)
        if len(self.replay_widgets) > 1:
            synchronize(widget, self.replay_widgets[0])
        
    @qtc.pyqtSlot(AbstractMediaPlayer)
    def widget_failed(self, widget):
        self.remove_replay_source(widget)
        
    def remove_replay_source(self, widget):
        self.replay_widgets.remove(widget)
        self.grid.removeWidget(widget)
        self.unsubscribe.emit(widget)
        widget.setParent(None)

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        # logging.info(f'QUERYING POSITION UPDATE IN {qtc.QThread.currentThread() = }')
        self.query_new_position.emit(pos)
    
    qtc.pyqtSlot(int)
    def solve_position_update(self, pos):
        assert qtc.QThread.currentThread() is self.thread_
        # logging.info(f'SOLVING POSITION UPDATE IN {qtc.QThread.currentThread() = }')
        if self.replay_widgets:
            main_widget = self.replay_widgets[0]
            main_widget.set_position(pos)
        self.synchronize()
         
    @qtc.pyqtSlot()
    def play(self):
        self.replay_speed_changed.emit(self.replay_speed)
        # logging.info(f'PLAY SIGNAL SENT from {qtc.QThread.currentThread() = }')
        self.setPaused.emit(False)
        
    @qtc.pyqtSlot()
    def pause(self):
        self.setPaused.emit(True)
    
    @qtc.pyqtSlot()
    def synchronize(self):
        assert qtc.QThread.currentThread() is self.thread_
        if self.replay_widgets:
            main_widget = self.replay_widgets[0]
            for w in self.replay_widgets[1:]:
                synchronize(w, main_widget)
    
    def init_timer(self):
        self.timer_thread = qtc.QThread()
        self.timer_worker = Timer()
        self.timer_worker.moveToThread(self.timer_thread)
        
        self.timer_thread.started.connect(self.timer_worker.run)
        self.timer_worker.finished.connect(self.timer_thread.quit)
        self.timer_worker.finished.connect(self.timer_worker.deleteLater)
        self.timer_thread.finished.connect(self.timer_thread.deleteLater)
        
        # connecting slots
        self.setPaused.connect(self.timer_worker.setPaused)
        self.reset.connect(self.timer_worker.reset)
        self.replay_speed_changed.connect(self.timer_worker.set_replay_speed)
        self.subscribe.connect(self.timer_worker.subscribe)
        self.unsubscribe.connect(self.timer_worker.unsubscribe)
        self.task_finished.connect(self.timer_worker.confirm_task)
        self.query_new_position.connect(self.timer_worker.set_position)
        self.stop_signal.connect(self.timer_worker.stop)
        
        self.timer_worker.timeout_signal.connect(self.on_timeout)
        self.timer_worker.change_position_signal.connect(self.solve_position_update)
        self.timer_worker.sync_needed.connect(self.synchronize)
        
    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self.stop_signal.emit()
        self.timer_thread.wait()
        return super().closeEvent(a0)
        
    @qtc.pyqtSlot(qtw.QWidget)
    def on_timeout(self, w):
        assert qtc.QThread.currentThread() is self.thread_
        # logging.info(f'SOLVING TIMEOUT FROM {qtc.QThread.currentThread() = }')
        w.on_timeout()
        self.task_finished.emit(w)
                       
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.replay_speed = x
        # self.timer_worker.set_replay_speed(x)
        self.replay_speed_changed.emit(self.replay_speed)
    
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
                    self.unsubscribe.emit(widget)
                    widget.fps = settings.refresh_rate
                    self.timer_worker.set_position(self.replay_widgets, self.replay_widgets[0].position)
                    self.subscribe.emit(widget) 
                
def time_in_millis():
    t = time.perf_counter()
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
