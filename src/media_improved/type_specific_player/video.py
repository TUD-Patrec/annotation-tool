import logging, cv2
import time
import numpy as np

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from ..player import AbstractMediaPlayer, AbstractMediaLoader, UpdateReason

class VideoPlayer(AbstractMediaPlayer):
    get_update = qtc.pyqtSignal(int, int, int, UpdateReason)
    media_loaded = qtc.pyqtSignal(object)
    
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
        self.loading_thread = VideoLoader(path)
        self.loading_thread.progress.connect(self.pbar.setValue)
        self.loading_thread.finished.connect(self._loading_finished)
        self.loading_thread.start()
    
    @qtc.pyqtSlot(cv2.VideoCapture)
    def _loading_finished(self, media):
        self.layout().replaceWidget(self.pbar, self.lblVid)
        
        self.pbar.setParent(None)
        del self.pbar
        
        self.fps = media.get(cv2.CAP_PROP_FPS)
        self.n_frames = int(media.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.media_loaded.emit(media)
        
        self.update_media_position(UpdateReason.OFFSET) # HACK
                       
        self.adjustSize()
        
        self.loaded.emit(self)
        
    """ 
    def update_media_position(self, update_reason: UpdateReason):
        pos = self.position + self.offset
        cap_pos = int(self.media.get(cv2.CAP_PROP_POS_FRAMES))
                
        if 0 <= pos < self.n_frames:
            if pos != cap_pos:
                # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does 
                # only manually update the cap_pos if we want to jump anywhere else
                self.media.set(cv2.CAP_PROP_POS_FRAMES, pos)
            self.next_frame()
        else:
            if pos < 0 and cap_pos != 1:
                logging.info('loading first frame as placeholder')
                self.media.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.next_frame()
            if pos >= self.n_frames and cap_pos != self.n_frames:
                logging.info('loading last frame as placeholder')
                self.media.set(cv2.CAP_PROP_POS_FRAMES, self.n_frames - 1)
                self.next_frame()
        self.send_ACK(update_reason)
        if update_reason == UpdateReason.TIMEOUT:
            self.emit_position()
       
        
    def next_frame(self):
        ret, frame = self.media.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            
            self.current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
            img = self.current_img.scaled(self.lblVid.width(), self.lblVid.height(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)
    """ 
    
    def resizeEvent(self, event):
        if self.current_img:
            qtw.QWidget.resizeEvent(self, event)
            self.lblVid.resize(event.size())
            img = self.current_img.scaled(self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)

    # not used right now   
    @qtc.pyqtSlot(qtg.QImage, qtg.QPixmap, UpdateReason)
    def update_ready(self, img, pix, update_reason):
        assert qtc.QThread.currentThread() is self.thread()
        logging.info('UPDATE READY')
        self.current_img = img
        self.lblVid.setPixmap(pix)
        
        self.send_ACK(update_reason)
        if update_reason == UpdateReason.TIMEOUT:
            self.emit_position()
                
   
    def update_media_position(self, update_reason: UpdateReason):
        assert qtc.QThread.currentThread() is self.thread()
        
        width, height = self.lblVid.width(), self.lblVid.height()
        pos = self.position + self.offset
        
        self.get_update.emit(width, height, pos, update_reason)
        logging.info('GET_UPDATE emitted')
    
    
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
        self.worker.update_ready.connect(self.update_ready)
        
        self.worker_thread.start()
        
    
     
# Not used right now   
class VideoHelper(qtc.QObject):
    update_ready = qtc.pyqtSignal(qtg.QImage, qtg.QPixmap, UpdateReason)
    finished = qtc.pyqtSignal()
     
    @qtc.pyqtSlot(object)
    def load_media(self, media):
        self.media = media
        logging.info(f'LOADED {self.media = }')
     
    @qtc.pyqtSlot(int, int, int, UpdateReason)
    def prepare_update(self, width, height, pos, update_reason):
        logging.info('t1')
        assert self.media is not None
        logging.info('t2')
        assert qtc.QThread.currentThread() is self.thread()
        logging.info(f'PREPARING UPDATE {pos = }')
        media = self.media
        cap_pos = int(media.get(cv2.CAP_PROP_POS_FRAMES))
        n_frames =  int(media.get(cv2.CAP_PROP_FRAME_COUNT))
                
        if 0 <= pos < n_frames:
            if pos != cap_pos:
                # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does 
                # only manually update the cap_pos if we want to jump anywhere else
                media.set(cv2.CAP_PROP_POS_FRAMES, pos)
        else:
            if pos < 0 and cap_pos != 1:
                logging.info('loading first frame as placeholder')
                media.set(cv2.CAP_PROP_POS_FRAMES, 0)
            elif pos >= n_frames and cap_pos != n_frames:
                logging.info('loading last frame as placeholder')
                media.set(cv2.CAP_PROP_POS_FRAMES, n_frames - 1)
            
        logging.info('177')
        assert 0 <= int(media.get(cv2.CAP_PROP_POS_FRAMES)) < n_frames
        logging.info('178')
        logging.info(f'{int(media.get(cv2.CAP_PROP_POS_FRAMES)) = }')

        # Loading image and pixmap
        ret, frame = media.read()
        logging.info('183')
        if ret:
            logging.info('ret_1')
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            logging.info('ret_2')
            h, w, ch = frame.shape
            logging.info('ret_3')
            bytes_per_line = ch * w
            logging.info('ret_4')
            current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
            logging.info('ret_5')
            img = current_img.scaled(width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            logging.info('ret_6')
            pix = qtg.QPixmap.fromImage(img)
            logging.info('ret_7')
        
            self.update_ready.emit(current_img, pix, update_reason)
            logging.info('193')
        else:
            logging.info('CRASHED')
            raise RuntimeError
               
    @qtc.pyqtSlot()       
    def stop(self):
        self.finished.emit()


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
    