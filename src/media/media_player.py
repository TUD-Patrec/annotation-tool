from abc import abstractmethod
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
from ..utility import filehandler

class TimerBasedMediaPlayer(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    loaded = qtc.pyqtSignal(qtw.QWidget)
    failed = qtc.pyqtSignal(qtw.QWidget)
    remove_wanted = qtc.pyqtSignal(qtw.QWidget)
    new_input_wanted = qtc.pyqtSignal(str)
    
    def __init__(self, *args, **kwargs) -> None:
        super(TimerBasedMediaPlayer, self).__init__(*args, **kwargs)
        
        # timer 
        self.timer = qtc.QTimer()
        self.timer.setTimerType(qtc.Qt.PreciseTimer)
        self.timer.timeout.connect(self.on_timeout)
        
        # controll atributes
        self.running_flag = False
        self.replay_speed = 1
        self.media = None
        self.fps = None
        self.n_frames = None
        self.position = 0
        self.offset = 0
        self.is_main_replay_widget = False
        
        # layout
        self.hbox = qtw.QHBoxLayout(self)
    
       
    def mousePressEvent(self, e):
        # leftclick = play/pause
        
        # rightclick = context_menu
        if e.button() == qtc.Qt.RightButton:
            menu = qtw.QMenu(self)
            
            menu.addAction(
                'Add another input source',
                self.add_input
            )
            
            if not self.is_main_replay_widget:
                menu.addAction(
                    'Remove input source',
                    self.remove_input
                )
                
                menu.addAction(
                    'Adjust offset',
                    self.adjust_offset
                )
                
            menu.popup(qtg.QCursor.pos())

    def set_main_replay_widget(self, x):
        self.is_main_replay_widget = bool(x)
    
    def add_input(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='Video MoCap (*.mp4 *.avi *.csv)')
        if filehandler.is_non_zero_file(filename):
            self.new_input_wanted.emit(filename)
    
    def remove_input(self):
        self.remove_wanted.emit(self)
    
    def adjust_offset(self):
        offset, ok = qtw.QInputDialog.getInt(self, 'Offset', 'Enter offset', value=self.offset)
        if ok:
            print('new offset ', offset)
            self.set_offset(offset)
        
     
    @abstractmethod
    @qtc.pyqtSlot(str)
    def load(self, input_file):
        raise NotImplementedError
    
    @qtc.pyqtSlot()
    def play(self):
        if self.media and self.fps and self.n_frames:
            self.running_flag = True
            millisecs = int(1000.0 / (self.replay_speed * self.fps))
            self.timer.setInterval(millisecs)
            self.timer.start()
    
    @qtc.pyqtSlot()
    def pause(self):
        self.running_flag = False
        self.timer.stop()
    
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, x):
        self.replay_speed = max(.01, x)
        millisecs = int(1000.0 / (self.replay_speed * self.fps))
        self.timer.setInterval(millisecs)
    
    @abstractmethod
    @qtc.pyqtSlot(int)
    def set_position(self, x):
        if x != self.position:
            self.position = x
            self.update_media_position()
      
    @qtc.pyqtSlot(int)
    def set_offset(self, x):
        self.offset = x
        self.update_media_position()

    @qtc.pyqtSlot()
    def on_timeout(self):
        self.position += 1
        self.update_media_position()
        pos = self.position + self.offset
        self.position_changed.emit(pos)
        
    @abstractmethod
    def update_media_position(self):
        raise NotImplementedError

    


        