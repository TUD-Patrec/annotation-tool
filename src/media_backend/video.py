import logging, cv2
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
        self.update_media_position(UpdateReason.OFFSET) # HACK
        self.loaded.emit(self)
            
    def resizeEvent(self, event):
        if self.current_img:
            qtw.QWidget.resizeEvent(self, event)
            self.lblVid.resize(event.size())
            img = self.current_img.copy().scaled(self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)

    # not used right now   
    @qtc.pyqtSlot(qtg.QImage, qtg.QPixmap, UpdateReason)
    def update_ready(self, img: qtg.QImage, pix: qtg.QPixmap, update_reason):
        assert qtc.QThread.currentThread() is self.thread()
        self.current_img = img
        self.lblVid.setPixmap(pix)
        self.adjustSize()
        self.confirm_update(update_reason)
    
    @qtc.pyqtSlot(UpdateReason)
    def no_update_needed(self, update_reason):
        logging.info('No updated required, correct frame already loaded')
        self.confirm_update(update_reason)
    
    @qtc.pyqtSlot(UpdateReason)
    def update_failed(self, update_reason):
        logging.info('Update failed')
        self.confirm_update(update_reason)
        
    def confirm_update(self, update_reason):
        self.send_ACK(update_reason)
        if update_reason == UpdateReason.TIMEOUT:
            self.emit_position()
            
    def update_media_position(self, update_reason: UpdateReason):
        assert qtc.QThread.currentThread() is self.thread()
        width, height = self.lblVid.width(), self.lblVid.height()
        pos = self.position + self.offset
        self.get_update.emit(width, height, pos, update_reason)
        
        
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
        self.worker.update_ready.connect(self.update_ready)
        self.worker.no_update_needed.connect(self.no_update_needed)
        self.worker.update_failed.connect(self.update_failed)
        
        self.worker_thread.start()
        
    def shutdown(self):
        logging.info('SHUTTING DOWN')
        self.stop_worker.emit()
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        logging.info('Thread cleaned up')
     
# Not used right now   
class VideoHelper(qtc.QObject):
    update_ready = qtc.pyqtSignal(qtg.QImage, qtg.QPixmap, UpdateReason)
    no_update_needed = qtc.pyqtSignal(UpdateReason)
    update_failed = qtc.pyqtSignal(UpdateReason)
    finished = qtc.pyqtSignal()
    
    @qtc.pyqtSlot(object)
    def load_media(self, media):
        self.media = media
        logging.info(f'LOADED {self.media = }')
     
    @qtc.pyqtSlot(int, int, int, UpdateReason)
    def prepare_update(self, width, height, pos, update_reason):
        assert self.media is not None
        assert qtc.QThread.currentThread() is self.thread()
        
        n_frames =  len(self.media)
        pos = max(0, min(n_frames, pos))
        
        frame = self.media[pos]
        frame = frame.asnumpy()
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
        if current_img.isNull():
            logging.info('current_img already Null')
            # Stop here in case of a Null-image
            self.update_failed.emit(update_reason)
            return
        
        # start = time.perf_counter()
        # Not sure why this is needed, but, just sending current_img somehow crashes
        # takes noticable time, might be too expensive
        # img_copy = current_img.copy()
        # end = time.perf_counter()
        # logging.info(f'{end - start = }')
        img = current_img.scaled(width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
        if img.isNull():
            logging.info('img is Null')
            # Stop here in case of a Null-image
            self.update_failed.emit(update_reason)
            return
            
        pix = qtg.QPixmap.fromImage(img)

        self.update_ready.emit(img, pix, update_reason)
        # self.update_ready.emit(img_copy, pix, update_reason)
    
               
    @qtc.pyqtSlot()       
    def stop(self):
        self.finished.emit()
        logging.info('STOPPING WORKER')


class VideoLoader(AbstractMediaLoader):
    def __init__(self, path) -> None:
        super().__init__(path)
    
    def load(self):
        try:
            self.media = cv2.VideoCapture(self.path)
        except:
            logging.error('Could NOT load the video from {}'.format(self.path))
            return
        if self.media.get(cv2.CAP_PROP_FRAME_COUNT) < 1:
            logging.error('EMPTY VIDEO LOADED')
    
    