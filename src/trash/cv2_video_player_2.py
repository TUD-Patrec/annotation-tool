import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

import sys, cv2, os

class VideoDisplayer(qtw.QWidget):
    """
    A QWidget for displaying videofiles.

    Attributes
    ----------
        video_path : os.PathLike
            Path to existing videofile.

    Signals
    -------
        video_loaded_successfully : bool
            emits a boolean value after trying to read the videofile.
        current_position_changed : (int,int)
            emits the tuple (current_position, total_frames).
        video_end_reached : ()
            emitted after the video has ended.
        replay_speed_changed : float
            emits the current replay_speed.
    
    Slots
    -----
        play_video():
            starts the video.
        pause_video():
            pauses the video.
        set_replay_speed(replay_speed):
            sets the replay_speed to a value at least as big as 0.1.
        skip_frames(n_frames):
            adds n_frames to the current_position and updates the displayed frame.
        set_position(pos):
            sets the current_position to pos and updates the displayed frame. 

    """

    video_loaded_successfully = qtc.pyqtSignal(bool)
    video_end_reached =  qtc.pyqtSignal()
    current_position_changed = qtc.pyqtSignal(int, int)
    replay_speed_changed = qtc.pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super(VideoDisplayer, self).__init__(*args, **kwargs)
        
        # controll-attribute
        self.cap = None
        self.total_frames = None
        self.current_position = None
        self.fps = None
        self.replay_speed = 1

        # setup timer
        self.timer = qtc.QTimer()
        self.timer.setTimerType(qtc.Qt.PreciseTimer)
        self.timer.timeout.connect(self.__next_frame_slot__)

        # main widget
        self.main_widget = qtw.QWidget()

        # video label
        self.lblVid = qtw.QLabel(self.main_widget)
        self.lblVid.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)

        # layout
        layout = qtw.QHBoxLayout()
        layout.addWidget(self.lblVid)
        self.setLayout(layout)


    @qtc.pyqtSlot(str)
    def load_video(self, path):
        try:
            self.cap = cv2.VideoCapture(path)
        except:
            print('Could NOT load the video from {}'.format(path))
            self.video_loaded_successfully.emit(False)

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.current_position = 0
        self.__sync__cap_with_current_position__()
        self.video_loaded_successfully.emit(True)


    @qtc.pyqtSlot()
    def play_video(self):
        millisecs = int(1000.0 / (self.replay_speed * self.fps))
        self.timer.start(millisecs)


    @qtc.pyqtSlot()
    def pause_video(self):
        self.timer.stop()


    @qtc.pyqtSlot(float)
    def set_replay_speed(self, replay_speed):
        replay_speed = max(.1, replay_speed)
        self.replay_speed = replay_speed
        millisecs = int(1000.0 / (self.replay_speed * self.fps))
        self.timer.setInterval(millisecs)
        self.replay_speed_changed.emit(self.replay_speed)
  

    @qtc.pyqtSlot(int)
    def skip_frames(self, n_frames):
        self.set_position(self.current_position + n_frames)
        

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        pos = max(0, pos)
        pos = min(self.total_frames-1, pos)
        self.current_position = pos
        self.__sync__cap_with_current_position__()
 
 # TODO
    @qtc.pyqtSlot(qtc.QTimer)
    def set_timer(self, timer):
        pass 


    def __sync__cap_with_current_position__(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_position-1)
        self.__next_frame_slot__(update_current_pos=False)
        #print(self.current_position, self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return


    def __next_frame_slot__(self, update_current_pos=True):
        if self.current_position < self.total_frames:
            ret, frame = self.cap.read()
            if ret == True:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = qtg.QImage(frame,frame.shape[1], frame.shape[0], qtg.QImage.Format_RGB888)
                pix = qtg.QPixmap.fromImage(img)           
                pix = pix.scaled(self.lblVid.width(), self.lblVid.height(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation)
                self.lblVid.setPixmap(pix)        

                self.current_position += int(update_current_pos)
                self.__signal_current_position__()
                
            else:
                raise RuntimeError('PLAYING VIDEO FAILED')
        else:
            self.video_end_reached.emit()


    def __signal_current_position__(self):
        self.current_position_changed.emit(self.current_position, self.total_frames)
    


"""
class VideoDisplayer(qtw.QWidget):
    video_loaded_successfully = qtc.pyqtSignal(bool)
    current_position = qtc.pyqtSignal(int)
    video_duration = qtc.pyqtSignal(int)

    def __init__(self, video_file, *args, **kwargs):
        super(VideoDisplayer, self).__init__(*args, **kwargs)
        self.video_path = video_file

        videowidget = QVideoWidget()

        #self.item = QGraphicsVideoItem()
        #self.item.setAspectRatioMode(qtc.Qt.KeepAspectRatio)
        #self.scene = qtw.QGraphicsScene(self)
        #self.scene.addItem(self.item)
        #self.scene.setBackgroundBrush(qtc.Qt.black)
        #self.view = qtw.QGraphicsView(self.scene)
        #self.view.setRenderHint(qtg.QPainter.Antialiasing, True)
        #self.view.setRenderHint(qtg.QPainter.SmoothPixmapTransform, True)
        #self.view.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        #self.view.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)

        self.media_player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        #self.media_player.setVideoOutput(self.item)
        self.media_player.setVideoOutput(videowidget)
        self.media_player.setMuted(True)

        self.media_player.setNotifyInterval(10)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(lambda x: print(x))

        #layout
        stack_ = qtw.QVBoxLayout()
        stack_.addWidget(videowidget)
        #stack_.addWidget(self.view)
        #verticalSpacer = qtw.QSpacerItem(20, 40, qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Expanding)
        #stack_.addWidget(verticalSpacer)
        self.setLayout(stack_)
        self.load_video()


    def load_video(self):
        #self.media_player.setMedia(QMediaContent(qtc.QUrl.fromLocalFile(self.video_path)))
        self.media_player.setMedia(QMediaContent(qtc.QUrl.fromLocalFile(self.video_path)))
        if True:
            print(self.media_player.mediaStatus())
            self.video_loaded_successfully.emit(True)

    def play_video(self, play):
        if play: 
            assert self.media_player.state() in [QMediaPlayer.PausedState, QMediaPlayer.StoppedState]
            self.media_player.play()
        else: 
            assert self.media_player.state() == QMediaPlayer.PlayingState
            self.media_player.pause()

    def position_changed(self, pos):
        self.current_position.emit(pos)

    def duration_changed(self, duration):       
        self.video_duration.emit(duration)
 
    def set_position(self, position):
        self.media_player.setPosition(position)

"""



if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    MainWindow = VideoDisplayer()
    MainWindow.resize(400,300)
    MainWindow.show()
    sys.exit(app.exec_())