import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw
import cv2
import numpy as np

from src.media.backend.player import AbstractMediaPlayer, UpdateReason
from src.media.video_reader import VideoReader


class VideoPlayer(AbstractMediaPlayer):
    get_update = qtc.pyqtSignal(int, int, int, UpdateReason)
    media_loaded = qtc.pyqtSignal(object)
    stop_worker = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.lblVid = qtw.QLabel(self)
        self.lblVid.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)
        self.lblVid.setAlignment(qtc.Qt.AlignCenter)
        self.layout().addWidget(self.lblVid)
        self.current_img = None

        # design
        p = self.palette()
        p.setColor(self.backgroundRole(), qtc.Qt.black)
        self.setPalette(p)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)

        self.init_worker()

    def load(self, path):
        media = VideoReader(path)
        self.fps = media.fps
        self.n_frames = len(media)
        self.media_loaded.emit(media)
        self.update_media_position(UpdateReason.INIT)
        self.loaded.emit(self)

    def resizeEvent(self, event):
        if self.current_img:
            qtw.QWidget.resizeEvent(self, event)
            self.lblVid.resize(event.size())
            img = self.current_img.scaled(
                self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation
            )
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

        self.current_img = qtg.QImage(
            frame, w, h, bytes_per_line, qtg.QImage.Format_RGB888
        )
        assert not self.current_img.isNull()

        pix = qtg.QPixmap.fromImage(img)
        self.lblVid.setPixmap(pix)

        if update_reason == UpdateReason.INIT:
            self.adjustSize()

        self.confirm_update(update_reason)

    @qtc.pyqtSlot(UpdateReason)
    def no_update_needed(self, update_reason):
        self.confirm_update(update_reason)

    def init_worker(self):
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
        self.n_frames = len(self.media)

    @qtc.pyqtSlot(int, int, int, UpdateReason)
    def prepare_update(self, pos, width, height, update_reason):
        assert self.media is not None
        assert qtc.QThread.currentThread() is self.thread()

        pos = max(0, min(self.n_frames - 1, pos))

        width_changed = width != self.last_width or height != self.last_height

        if pos == self.last_position and not width_changed:
            # no update needed
            self.no_update_needed.emit(update_reason)
            return

        self.last_position = pos
        self.last_width = width
        self.last_height = height

        # Loading image and pixmap
        frame = self.media[pos]
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            h, w, ch = frame.shape
            bytes_per_line = ch * w

            current_img = qtg.QImage(
                frame, w, h, bytes_per_line, qtg.QImage.Format_RGB888
            )
            img = current_img.scaled(
                width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation
            )

            self.image_ready.emit(img, frame, w, h, bytes_per_line, update_reason)

        else:
            self.no_update_needed.emit(update_reason)

    @qtc.pyqtSlot()
    def stop(self):
        self.finished.emit()
