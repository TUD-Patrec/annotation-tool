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
        media = self.media
        cap_pos = int(media.get(cv2.CAP_PROP_POS_FRAMES))
        n_frames =  int(media.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Default case: Updating the media-position if necessary (remember that media.read() automatically increments the position by 1)
        if 0 <= pos < n_frames:
            if pos != cap_pos:
                # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does 
                # only manually update the cap_pos if we want to jump anywhere else
                media.set(cv2.CAP_PROP_POS_FRAMES, pos)
        else:
            # Case 2: Due to some offset, or this video not being alignigned with the reference video, we're at a position where this video has not started yet (pos < 0) or is already over (pos >= n_frames) 
            if pos < 0 and cap_pos != 1:
                # Case 2.1: The video has not yet started and the currently displayed frame is not the first one -> load the first frame as a placeholder
                logging.info('loading first frame as placeholder')
                media.set(cv2.CAP_PROP_POS_FRAMES, 0)
            elif pos >= n_frames and cap_pos != n_frames:
                # Case 2.2: The video is over and the currently displayed frame is not the last one -> load the last frame as a placeholder
                logging.info('loading last frame as placeholder')
                media.set(cv2.CAP_PROP_POS_FRAMES, n_frames - 1)
            else:
                # Case 2.3: The current position is out of the videos bounds, but the correct frame is already being displayed -> nothing to do; return
                self.no_update_needed.emit(update_reason)
                return
            
        assert 0 <= int(media.get(cv2.CAP_PROP_POS_FRAMES)) < n_frames, f'{int(media.get(cv2.CAP_PROP_POS_FRAMES)) = }, {n_frames = }'
        
        # Loading image and pixmap
        ret, frame = media.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            logging.info(f'{frame.shape = }')
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
                        
            start = time.perf_counter()
            # Not sure why this is needed, but, just sending current_img somehow crashes the tool
            # takes approx 2ms, might be too expensive
            img_copy = current_img.copy()
            end = time.perf_counter()
            # logging.info(f'{end - start = }')
            img = current_img.scaled(width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            # assert not (img is None or img.isNull())
            if img.isNull():
                # Stop here in case of a Null-image
                self.update_failed.emit(update_reason)
                return
                
            pix = qtg.QPixmap.fromImage(img)

            # self.update_ready.emit(img, pix, update_reason)
            self.update_ready.emit(img_copy, pix, update_reason)
        else:
            logging.error('CRASHED')
            raise RuntimeError
               
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
    
    