import logging, cv2
from re import U
from decord import VideoReader
import time
import numpy as np

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from ..player import AbstractMediaPlayer, AbstractMediaLoader, UpdateReason

class VideoPlayer(AbstractMediaPlayer):
    get_update = qtc.pyqtSignal(int, int, int, UpdateReason)
    media_loaded = qtc.pyqtSignal(object)
    stop_worker = qtc.pyqtSignal()
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.lblVid = qtw.QLabel(self)
        self.lblVid.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)
        self.lblVid.setAlignment(qtc.Qt.AlignCenter)
        self.current_img = None
               
        # design 
        p = self.palette()
        p.setColor(self.backgroundRole(), qtc.Qt.black)
        self.setPalette(p)
        self.layout().setContentsMargins(0,0,0,0)
        self.setAutoFillBackground(True)
                
        self.init_worker()
    
    def load(self, path):
        vr = VideoReader(path)
        self.layout().replaceWidget(self.pbar, self.lblVid)
        self.pbar.setParent(None)
        del self.pbar
        self.fps = vr.get_avg_fps()
        self.n_frames = len(vr)
        self.media_loaded.emit(vr)
        self.update_media_position(UpdateReason.INIT)
        self.loaded.emit(self)
            
    def resizeEvent(self, event):
        if self.current_img:
            qtw.QWidget.resizeEvent(self, event)
            self.lblVid.resize(event.size())
            img = self.current_img.scaled(self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)
    
    def update_media_position(self, update_reason: UpdateReason):
        assert qtc.QThread.currentThread() is self.thread()
        
        width, height = self.lblVid.width(), self.lblVid.height()
        pos = self.position + self.offset
        self.get_update.emit(pos, width, height, update_reason)
    
    @qtc.pyqtSlot(qtg.QImage, np.ndarray, int, int, int, UpdateReason)
    def image_ready(self, img, frame, w, h, bytes_per_line, update_reason):     
        if img.isNull():   
            # Currently loading another video/replay_source
            self.confirm_update(update_reason)
            return
        
        self.current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
        assert not self.current_img.isNull()
        
        pix = qtg.QPixmap.fromImage(img)
        self.lblVid.setPixmap(pix)
        
        if update_reason == UpdateReason.INIT:
            self.adjustSize()
        
        self.confirm_update(update_reason)

    @qtc.pyqtSlot(UpdateReason)
    def no_update_needed(self, update_reason):
        self.confirm_update(update_reason)
        
    def confirm_update(self, update_reason):
        self.send_ACK(update_reason)
        logging.info(f'{self.position}')
        if update_reason == UpdateReason.TIMEOUT:
            self.emit_position()
    
    def init_worker(self):
        logging.info('INIT Worker Thread')
        self.worker_thread = qtc.QThread()
        self.worker = VideoHelper()
        self.worker.moveToThread(self.worker_thread)
        
        # connecting worker and thread
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
                
        # connecting to worker
        self.get_update.connect(self.worker.prepare_update)
        self.media_loaded.connect(self.worker.load_media)
        self.stop_worker.connect(self.worker.stop)
        self.worker.no_update_needed.connect(self.no_update_needed)
        self.worker.image_ready.connect(self.image_ready)
        
        self.worker_thread.start()
         
    def shutdown(self):
        assert qtc.QThread.currentThread() is self.thread()
        self.stop_worker.emit()
        self.worker_thread.quit()
        self.worker_thread.wait()

    
class VideoHelper(qtc.QObject):
    image_ready = qtc.pyqtSignal(qtg.QImage, np.ndarray, int, int, int, UpdateReason)
    no_update_needed = qtc.pyqtSignal(UpdateReason)
    finished = qtc.pyqtSignal()
    
    @qtc.pyqtSlot(object)
    def load_media(self, media):
        self.media = media
        self.last_position = -1
        self.last_width = -1
        self.last_height = -1 
        self.n_frames = len(media)
     
    @qtc.pyqtSlot(int, int, int, UpdateReason)
    def prepare_update(self, pos, width, height, update_reason):
        assert self.media is not None
        assert qtc.QThread.currentThread() is self.thread()
        
        pos = max(0, min(self.n_frames - 1, pos))

        width_changed = width != self.last_width or height != self.last_height
        
        if pos == self.last_position and not width_changed:
            self.no_update_needed.emit(update_reason)
        else: 
            logging.info(f'{pos = }')
            self.last_position = pos
            self.last_width = width
            self.last_height = height
            
            #before = time.perf_counter()
            #self.media.seek_accurate(pos)
            #after = time.perf_counter()
            #logging.info(f'DELTA  = {after - before}')

            frame = self.media[pos].asnumpy()
            logging.info(f'{len(self.media) = }')
                        
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            
            current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
            img = current_img.scaled(width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation) # Somehow this is faster
            # img = self.current_img.scaled(self.lblVid.width(), self.lblVid.height(), qtc.Qt.KeepAspectRatio, qtc.Qt.FastTransformation) 
            
            self.image_ready.emit(img, frame, w, h, bytes_per_line, update_reason)
        
    @qtc.pyqtSlot()       
    def stop(self):
        self.finished.emit()


    