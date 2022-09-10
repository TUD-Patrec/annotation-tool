from abc import abstractmethod, ABC
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
from ..utility import filehandler
from ..utility.decorators import accepts, returns
from enum import Enum
import logging


class UpdateReason(Enum):
    TIMEOUT = 1
    SETPOS = 2
    OFFSET = 3


class AbstractMediaPlayer(qtw.QWidget):
    remove_wanted =  qtc.pyqtSignal(qtw.QWidget)    # Emit self to be removed
    new_input_wanted = qtc.pyqtSignal(str)          # Path to new input-file
    loaded = qtc.pyqtSignal(qtw.QWidget)            # Emit self to notify controller about successfull loading
    failed = qtc.pyqtSignal(qtw.QWidget)            # Emit self to notify controller about failed loading
    ACK_timeout = qtc.pyqtSignal(qtw.QWidget)       # Confirm timeout processed
    ACK_setpos = qtc.pyqtSignal(qtw.QWidget)        # Confirm set_positon processed
    position_changed = qtc.pyqtSignal(int)          # Broadcast position after change
    
    def __init__(self, is_main, *args, **kwargs):
        super(AbstractMediaPlayer, self).__init__(*args, **kwargs)
        
        # media 
        self._media = None     
        
        # media controll attributes
        self._fps = None 
        self._n_frames = None
        self._position = 0 
        self._offset = 0
        
        # distinct between primary player and added ones
        self._is_main_replay_widget = is_main

        # layout 
        self.init_layout()
                
        # Thread saftey
        self._mutex_fps = qtc.QMutex()
        self._mutex_n_frames = qtc.QMutex()
        self._mutex_position = qtc.QMutex()
        self._mutex_offset = qtc.QMutex()
    
    def init_layout(self):
        self.hbox = qtw.QHBoxLayout(self)
        self.pbar = qtw.QProgressBar(self)
        self.pbar.setValue(0)
        self.pbar.setRange(0, 100)
        self.hbox.addWidget(self.pbar)
       
    def mousePressEvent(self, e): 
        # rightclick = context_menu
        if e.button() == qtc.Qt.RightButton:
            self.open_context_menu()

    def open_context_menu(self):
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
     
    def shutdown(self):
        pass
           
    @qtc.pyqtSlot()    
    def add_input(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(directory='', filter='Video MoCap (*.mp4 *.avi *.csv)')
        if filehandler.is_non_zero_file(filename):
            self.new_input_wanted.emit(filename)
    
    @qtc.pyqtSlot()  
    def remove_input(self):
        self.remove_wanted.emit(self)
    
    @qtc.pyqtSlot()    
    def adjust_offset(self):
        offset, ok = qtw.QInputDialog.getInt(self, 'Offset', 'Enter offset', value=self.offset)
        if ok:
            self.offset = offset
            self.update_media_position(UpdateReason.OFFSET)
        
    @abstractmethod
    @qtc.pyqtSlot(str)
    def load(self, input_file):
        raise NotImplementedError
    
    @qtc.pyqtSlot(qtw.QWidget)
    def on_timeout(self, w):
        if self is w:
            self.position += 1
            self.update_media_position(UpdateReason.TIMEOUT)
    
    @qtc.pyqtSlot(qtw.QWidget, int)
    def set_position(self, w, x):
        if self is w:
            update_needed = x != self.position
            if update_needed:
                self.position = x
                self.update_media_position(UpdateReason.SETPOS)
            else:
                # Short circuting if no position change has happened
                # Still need to senc ACK 
                self.send_ACK(UpdateReason.SETPOS)
            
    @qtc.pyqtSlot()
    def ack_timeout(self):
        self.ACK_timeout.emit(self)
        
    @qtc.pyqtSlot()
    def ack_position_update(self):
        self.ACK_setpos.emit(self) 
     
    def send_ACK(self, r):
        if r == UpdateReason.TIMEOUT:
            self.ACK_timeout.emit(self)
        if r == UpdateReason.SETPOS:
            self.ACK_setpos.emit(self)
    
    @abstractmethod
    def update_media_position(self, reason: UpdateReason):
        raise NotImplementedError
    
    def emit_position(self):
        if self._is_main_replay_widget:
            assert self.offset == 0 # offset must not be changed for the main replay widget
            self.position_changed.emit(self.position)

    # Thread safe getter and setter
    # Settings properties is only allowed from the main GUI-Thread - see assertions
    @property 
    def media(self):
        # Need to asure that the media object is not accessed from another thread
        # Implement thread-secure methods for accessing media-informations (reading a frame for example)
        assert qtc.QThread.currentThread() is self.thread()
        return self._media
    
    @media.setter
    def media(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self._media = x
    
    @property
    @returns((int, float))
    def fps(self):
        self._mutex_fps.lock()
        x = self._fps
        self._mutex_fps.unlock()
        return x
    
    @fps.setter
    @accepts(qtw.QWidget, (int, float))
    def fps(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        assert 0 < x
        self._mutex_fps.lock()
        self._fps = x
        self._mutex_fps.unlock()
     
    @property
    @returns(int)   
    def position(self):
        self._mutex_position.lock()
        x = self._position
        self._mutex_position.unlock()
        return x
    
    @position.setter
    @accepts(qtw.QWidget, int)
    def position(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        assert 0 <= x
        self._mutex_position.lock()
        self._position = x
        self._mutex_position.unlock()
        
    @property
    @returns(int)
    def n_frames(self):
        self._mutex_n_frames.lock()
        x = self._n_frames
        self._mutex_n_frames.unlock()
        return x

    @n_frames.setter
    @accepts(qtw.QWidget, int)
    def n_frames(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        assert 0 <= x
        self._mutex_n_frames.lock()
        self._n_frames = x
        self._mutex_n_frames.unlock()
    
    @property
    @returns(int)
    def offset(self):
        self._mutex_offset.lock()
        x = self._offset        
        self._mutex_offset.unlock()
        return x
     
    @offset.setter
    @accepts(qtw.QWidget, int)   
    def offset(self, x):
        assert qtc.QThread.currentThread() is self.thread()
        self._mutex_offset.lock()
        self._offset = x
        self._mutex_offset.unlock()
    
    @property
    @returns(bool)
    def is_main_replay_widget(self):
        return self._is_main_replay_widget
    
    

class AbstractMediaLoader(qtc.QThread):
    progress = qtc.pyqtSignal(int)
    finished = qtc.pyqtSignal(object)
    
    def __init__(self, path:str) -> None:
        super().__init__()
        self.path = path
        self.media = None
        
    def run(self):
        self.load()
        self.finished.emit(self.media)

 
    @abstractmethod
    def load(self):
        raise NotImplementedError
    
