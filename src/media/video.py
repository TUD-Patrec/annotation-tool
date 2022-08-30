import logging, cv2

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from .media_player import TimerBasedMediaPlayer

class VideoPlayer(TimerBasedMediaPlayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.lblVid = qtw.QLabel(self)
        self.lblVid.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)
        self.lblVid.setAlignment(qtc.Qt.AlignCenter)

        self.layout().addWidget(self.lblVid)
        
        # design 
        p = self.palette()
        p.setColor(self.backgroundRole(), qtc.Qt.black)
        self.setPalette(p)
        self.layout().setContentsMargins(0,0,0,0)
        self.setAutoFillBackground(True)
        
        
    def load(self, input_file):
        try:
            self.media = cv2.VideoCapture(input_file)
        except:
            print('Could NOT load the video from {}'.format(input_file))
            self.failed.emit(self)
            return
        if self.media.get(cv2.CAP_PROP_FRAME_COUNT) < 1:
            print('EMPTY VIDEO LOADED')
            self.failed.emit(self)
            return
        self.fps = self.media.get(cv2.CAP_PROP_FPS)
        self.n_frames = int(self.media.get(cv2.CAP_PROP_FRAME_COUNT))
        self.next_frame()
        width = self.media.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
        height = self.media.get(cv2.CAP_PROP_FRAME_HEIGHT)
        logging.info('Video-Shape: {} x {}.'.format(width, height))
        self.loaded.emit(self)
    
    def update_media_position(self):
        cap_pos = int(self.media.get(cv2.CAP_PROP_POS_FRAMES))
        pos = self.position + self.offset
                
        if 0 <= pos < self.n_frames:
            if pos != cap_pos:
                # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does 
                # only manually update the cap_pos if we want to jump anywhere else
                self.media.set(cv2.CAP_PROP_POS_FRAMES, pos)
            self.next_frame()
        else:
            if pos < 0 and cap_pos != 1:
                self.media.set(cv2.CAP_PROP_POS_FRAMES, pos)
                self.next_frame()
            if pos >= self.n_frames and cap_pos != self.n_frames:
                self.media.set(cv2.CAP_PROP_POS_FRAMES, pos)
                self.next_frame()
        
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
    
    def resizeEvent(self, event):
        qtw.QWidget.resizeEvent(self, event)
        self.lblVid.resize(event.size())
        img = self.current_img.scaled(self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
        pix = qtg.QPixmap.fromImage(img)
        self.lblVid.setPixmap(pix)