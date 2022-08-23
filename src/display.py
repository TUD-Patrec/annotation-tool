import logging, sys, cv2

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import functools

from .utility.functions import FrameTimeMapper

from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget

class VideoDisplayerF(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    video_loaded = qtc.pyqtSignal(qtw.QWidget)
    video_failed = qtc.pyqtSignal(qtw.QWidget)
        
    def __init__(self, *args, **kwargs):
        super(VideoDisplayerF, self).__init__(*args, **kwargs)
        
        # controll-attributes
        self.cap = None
        self.running_flag = False
        self.current_img = None
        
        # timer
        self.timer = qtc.QTimer()
        self.timer.setTimerType(qtc.Qt.PreciseTimer)
        self.timer.timeout.connect(self.on_timeout)
        self.replay_speed = 1

        # video label
        self.lblVid = qtw.QLabel(self)
        self.lblVid.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)
       
        #layout
        layout = qtw.QHBoxLayout()
        layout.addWidget(self.lblVid)
        self.setLayout(layout)
        
        p = self.palette()
        p.setColor(self.backgroundRole(), qtc.Qt.black)
        self.setPalette(p)
        
        self.layout().setContentsMargins(0,0,0,0)
        self.lblVid.setAlignment(qtc.Qt.AlignCenter)
        
        self.setAutoFillBackground(True)
        
    # TODO MORE Boundaries to check
    @qtc.pyqtSlot(float) 
    def set_replay_speed(self, replay_speed):
        self.replay_speed = max(.01, replay_speed)
        if self.cap != None:
            self.__update_timer__()

    @qtc.pyqtSlot()
    def play(self):
        if self.cap is not None:
            self.running_flag = True
            self.__update_timer__()
            self.timer.start()
    
    @qtc.pyqtSlot()
    def pause(self):
        self.running_flag = False
        self.timer.stop()
    
    def __update_timer__(self):
        millisecs = int(1000.0 / (self.replay_speed * self.__get_fps__()))
        self.timer.setInterval(millisecs)
    
    @qtc.pyqtSlot(str)
    def load_video(self, path):
        try:
            self.cap = cv2.VideoCapture(path)
        except:
            print('Could NOT load the video from {}'.format(path))
            self.video_failed.emit(self)
            return
        if self.cap.get(cv2.CAP_PROP_FRAME_COUNT) < 1:
            print('EMPTY VIDEO LOADED')
            self.video_failed.emit(self)
            return
        self.next_frame()
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        logging.info('Video-Shape: {} x {}.'.format(width, height))
        self.video_loaded.emit(self)
    
    def resizeEvent(self, event):
        qtw.QWidget.resizeEvent(self, event)
        #print('BEFORE:', self.size())
        #print(event.size())
        self.lblVid.resize(event.size())
        img = self.current_img.scaled(self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
        pix = qtg.QPixmap.fromImage(img)
        self.lblVid.setPixmap(pix)
    
    def __get_total_frame_count__(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def __get_position__(self):
        return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def __get_fps__(self):
        return self.cap.get(cv2.CAP_PROP_FPS)
    
    def on_timeout(self):
        # the cap-position is always 1 pointing to the NEXT frame-index -> emitting the cap-pos BEFORE the update is the actually correct
        current_position = self.__get_position__()
        self.next_frame()
        self.position_changed.emit(current_position)
    
    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        cap_pos = self.__get_position__()
        if new_pos != cap_pos:
            # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does 
            # only manually update the cap_pos if we want to jump anywhere else
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        self.next_frame()

    def next_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            
            self.current_img = qtg.QImage(frame,  w, h, bytes_per_line, qtg.QImage.Format_RGB888)
            img = self.current_img.scaled(self.lblVid.width(), self.lblVid.height(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)
        

class VideoPlayerT(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    video_loaded = qtc.pyqtSignal(qtw.QWidget)
    video_failed = qtc.pyqtSignal(qtw.QWidget)
    
    def __init__(self, *args, **kwargs):
        super(VideoPlayerT, self).__init__(*args, **kwargs)
        self.mediaPlayer = QMediaPlayer(self, QMediaPlayer.VideoSurface)

        self.videoWidget = QVideoWidget()
        self.loaded = False

        layout = qtw.QHBoxLayout()
        layout.addWidget(self.videoWidget)
        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.positionChanged.connect(self.pos_changed)
        self.mediaPlayer.mediaStatusChanged.connect(self.media_status_changed)
        self.mediaPlayer.durationChanged.connect(lambda x: logging.info('duration = {}'.format(x)))
        
        self.mediaPlayer.error.connect(self.on_error)

    @qtc.pyqtSlot(str)
    def load_video(self, path):
        self.loaded = False
        logging.info(path)
        self.mediaPlayer.setMedia(QMediaContent(qtc.QUrl.fromLocalFile(path)))
    
    def on_error(self, idx):
        self.video_failed.emit(self)
     
    def media_status_changed(self):
        status = self.mediaPlayer.mediaStatus()
        logging.info('Media_Status = {}'.format(status))
        
        if QMediaPlayer.mediaStatus == QMediaPlayer.InvalidMedia:
            self.video_failed.emit(self)
        
        # Loaded
        if status == 3 and not self.loaded:
            self.play()
            self.pause()
            self.set_position(0)
            self.loaded = True
            for x in self.mediaPlayer.availableMetaData():
                logging.info('{} = {}'.format(x, self.mediaPlayer.metaData(x)))
            try:
                fps = self.mediaPlayer.metaData('VideoFrameRate')
            except:
                fps = 100
            logging.info('FPS = {}'.format(fps))
            
            self.mediaPlayer.setNotifyInterval(int(1000 / (3 * fps)))
            self.video_loaded.emit(self)
     
    def pos_changed(self, pos):
        pos = int(pos)
        pos = FrameTimeMapper.instance().ms_to_frame(pos)
        self.position_changed.emit(pos)
     
    @qtc.pyqtSlot()   
    def play(self):
        self.mediaPlayer.play()

    @qtc.pyqtSlot()
    def pause(self):
        self.mediaPlayer.pause()
        frame_pos = FrameTimeMapper.instance().ms_to_frame(self.mediaPlayer.position())
        self.set_position(frame_pos)
        self.position_changed.emit(frame_pos)
    
    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        new_pos = FrameTimeMapper.instance().frame_to_ms(new_pos)
        self.mediaPlayer.setPosition(new_pos)
        
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, replay_speed):
        self.mediaPlayer.setPlaybackRate(replay_speed)
        

class QMediaMainController(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(QMediaMainController, self).__init__(*args, **kwargs)
        self.replay_widgets = []
        # self.replay_offsets = [] # possibly needed later for extension to multi-video

        # layout
        grid = qtw.QGridLayout()
        self.setLayout(grid)

    @qtc.pyqtSlot(str)
    def load(self, annotation):
        path = annotation.input_file
        file_ext = path.split('.')[-1]
        if file_ext in ['mp4', 'avi']:
            self._load_video(path, use_frames=annotation.frame_based_annotation)
        if file_ext in ['csv']:
            self.__load_mocap__(path)

    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        for repl in self.replay_widgets:
            repl.set_position(new_pos)

    @qtc.pyqtSlot()
    def play(self):
        for repl in self.replay_widgets:
            repl.play()
    
    @qtc.pyqtSlot()
    def pause(self):
        for repl in self.replay_widgets:
            repl.pause()
    
    @qtc.pyqtSlot(float)
    def set_replay_speed(self, replay_speed):
        for repl in self.replay_widgets:
            repl.set_replay_speed(replay_speed)
    
    # TODO
    def __load_mocap__(self, path):
        pass
    
    def _video_loaded(self, widget):
        logging.info('LOADING VIDEO SUCCEEDED!')
        self.replay_widgets.append(widget)
        widget.position_changed.connect(self.position_changed)
        self.layout().addWidget(widget)
    
    def _video_failed(self, path,  widget):
        logging.warning('Loading Video failed for {} of type{}'.format(widget, type(widget)))
        
        # Default to frame based player
        alternative_player = VideoDisplayerF(self)
        alternative_player.load_video(path)
        alternative_player.video_failed.connect(lambda _: self.on_error())
        alternative_player.video_loaded.connect(self._video_loaded)
        
        self.replay_widgets.append(alternative_player)
        self.layout().addWidget(alternative_player)
        
    def on_error(self):
        raise RuntimeError()

    def _load_video(self, path, use_frames=True):
        for w in self.replay_widgets:
            self.layout().removeWidget(w)

        self.replay_widgets = []
        
        if use_frames:
            vid_player = VideoDisplayerF(self)
        else:
            vid_player = VideoPlayerT(self)
        
        fail = functools.partial(self._video_failed, path)
        
        vid_player.video_failed.connect(fail)
        vid_player.video_loaded.connect(self._video_loaded)
        
        vid_player.load_video(path)


    """  
    maybe add support for multi camera - load multiple sources, synchronize them, etc.
    Currently no priority
    # TODO
    qtc.pyqtSlot(str)
    def __add_video__(self, video_path):
        if len(self.replay_widgets) <= self.video_widgets_allowed:
            vid_player = VideoDisplayer()
            self.layout().addWidget(vid_player)
            vid_player.load_video(video_path)

            self.replay_widgets.append(vid_player)

            if self.slots_used >= 1:
                ofs = self.__sync_videos__(vid_player)
                self.replay_offsets.append(ofs)
                vid_player.set_offset(ofs)

            else:
                self.replay_offsets.append(0)           
            self.slots_used += 1
            self.__reshape_grid__()
            
        else:
            print('DISPLAY IS FULL - no more replay-sources can be added')
    
    # TODO
    def __update_offsets__(self):
        for repl, ofs in zip(self.replay_widgets, self.replay_offsets):
            repl.set_offset(ofs)
            repl.jump_to_frame(self.position)

    # TODO
    @qtc.pyqtSlot(list)
    def __set_offsets__(self, offsets):
        assert len(offsets) == len(self.replay_offsets)
        self.replay_offsets = offsets
        self.__update_offsets__()           # Hide implementation detail

    # TODO
    def __sync_videos__(self, vid_player):
        return 0

    # TODO
    qtc.pyqtSlot(int,int)
    def __remove_replay_source__(self, replay_widget: Tuple[int,int]):
        #self.slots_used -= 1
        self.layout().removeWidget(replay_widget)
        
    # TODO
    def __reshape_grid__(self):
        pass

    # TODO
    @qtc.pyqtSlot()
    def __error_on_frame_update_handler__(self):
        pass

    """


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    MainWindow = VideoPlayerT()
    MainWindow.resize(400,300)
    MainWindow.load_video('C:\\Users\\Raphael\\Desktop\\S07_Brownie_7150991-1431.avi')
    MainWindow.play()
    MainWindow.show()
    sys.exit(app.exec_())