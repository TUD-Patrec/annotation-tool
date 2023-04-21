import logging
from threading import Thread
from time import sleep

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.media.backend.player import AbstractMediaPlayer
from annotation_tool.media_reader import media_reader as mr


def check_resize(vp):
    w, h = vp.lblVid.width(), vp.lblVid.height()
    while True:
        try:
            active = vp._active  # noqa
        except:  # noqa
            break
        if not active:
            break
        if w != vp.lblVid.width() or h != vp.lblVid.height():
            vp.get_update.emit()
            w, h = vp.lblVid.width(), vp.lblVid.height()
        sleep(0.1)


class VideoPlayer(AbstractMediaPlayer):
    get_update = qtc.pyqtSignal()
    media_loaded = qtc.pyqtSignal(object)
    load_worker = qtc.pyqtSignal(str)
    stop_worker = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.lblVid = qtw.QLabel(self)
        self.lblVid.setSizePolicy(
            qtw.QSizePolicy.Policy.Ignored, qtw.QSizePolicy.Policy.Ignored
        )
        self.lblVid.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.lblVid)

        # design
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.worker_thread = qtc.QThread()
        self.worker = VideoHelper(self)
        self.init_worker()

        self._active = True

        self.resize_worker = Thread(target=check_resize, args=(self,), daemon=True)
        self.resize_worker.start()

    def load(self, path):
        self.load_worker.emit(path)

    @qtc.pyqtSlot(float, int)
    def worker_loaded(self, fps, n_frames):
        self.fps = fps
        self.n_frames = n_frames
        self.loaded.emit(self)
        self.adjustSize()

    def update_media_position(self):
        self.get_update.emit()

    @qtc.pyqtSlot(qtg.QPixmap)
    def update_pixmap(self, pix):
        self.lblVid.setPixmap(pix)

    def init_worker(self):
        self.worker.moveToThread(self.worker_thread)

        # connecting to worker
        self.load_worker.connect(self.worker.load)
        self.get_update.connect(self.worker.update)
        self.worker.image_ready.connect(self.update_pixmap)
        self.worker.loaded.connect(self.worker_loaded)
        self.stop_worker.connect(self.worker.stop)

        # setup nice exit
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.thread_finished)

        self.worker_thread.start()

    def thread_finished(self):
        logging.debug("VideoPlayer: Thread finished.")
        self.terminated = True
        self.worker = None
        self.worker_thread = None
        self.finished.emit(self)

    @qtc.pyqtSlot()
    def shutdown(self):
        self._active = False
        # disconnect relevant signals
        self.get_update.disconnect()  # dont forward updates to worker
        self.worker.image_ready.disconnect()  # dont update pixmap anymore
        self.lblVid.clear()  # clear pixmap
        self.stop_worker.emit()

    def kill(self):
        """
        This is called when the tool is closed.
        --> This will block the main thread until the worker thread is finished.
        Use shutdown instead if you only want to remove the widget from the screen.
        """
        if self.worker_thread is not None:
            try:
                self.worker.kill()
                assert self.worker.is_finished()
            except RuntimeError:
                logging.debug("VideoPlayer: VideoHelper already dead.")
            self.worker = None
        if self.worker_thread is not None:
            try:
                self.worker_thread.quit()
                self.worker_thread.wait()
            except RuntimeError:
                logging.debug("VideoPlayer: Worker-Thread already terminated.")
            self.worker_thread = None


class VideoHelper(qtc.QObject):
    image_ready = qtc.pyqtSignal(qtg.QPixmap)
    loaded = qtc.pyqtSignal(float, int)
    finished = qtc.pyqtSignal()

    def __init__(self, video_player: VideoPlayer):
        super().__init__()
        self._video_player = video_player
        self.media = None

        self._last_img = None
        self._finished = False

        self._last_pos = -9999999
        self._last_w = -1
        self._last_h = -1

    @qtc.pyqtSlot(str)
    def load(self, path):
        self.media = mr(path)
        self.loaded.emit(self.fps, self.n_frames)

    @property
    def n_frames(self):
        if self.media:
            return len(self.media)

    @property
    def fps(self):
        if self.media:
            return self.media.fps

    @property
    def path(self):
        if self.media:
            return self.media.path

    @qtc.pyqtSlot()
    def update(self):
        if self._finished:
            return
        self.__update__()

    def __update__(self):
        pos = self._video_player.position + self._video_player.offset
        width, height = (
            self._video_player.lblVid.width(),
            self._video_player.lblVid.height(),
        )

        pos = max(0, min(self.n_frames - 1, pos))

        dims_changed = width != self._last_w or height != self._last_h
        pos_changed = pos != self._last_pos

        if not pos_changed and not dims_changed:
            # no update needed
            return

        self._last_pos = pos
        self._last_w = width
        self._last_h = height

        if not pos_changed:
            # only dims changed
            img = self._last_img
            img = img.scaled(
                width,
                height,
                qtc.Qt.AspectRatioMode.KeepAspectRatio,
                qtc.Qt.TransformationMode.SmoothTransformation,
            )
            pix = qtg.QPixmap.fromImage(img)

            try:
                self.image_ready.emit(pix)
            except RuntimeError:
                # widget already deleted
                pass
            return

        # full update
        frame = self.media[pos]  # Loading image and pixmap
        if frame is not None:

            h, w, ch = frame.shape
            bytes_per_line = ch * w

            img = qtg.QImage(
                frame, w, h, bytes_per_line, qtg.QImage.Format.Format_RGB888
            )

            self._last_img = img  # keep a reference to the image

            img = img.scaled(
                width,
                height,
                qtc.Qt.AspectRatioMode.KeepAspectRatio,
                qtc.Qt.TransformationMode.SmoothTransformation,
            )
            pix = qtg.QPixmap.fromImage(img)

            try:
                self.image_ready.emit(pix)
            except RuntimeError:
                pass  # widget already deleted

    @qtc.pyqtSlot()
    def stop(self):
        self._finished = True
        # self._video_player = None
        self.finished.emit()
        logging.info("VideoHelper: finished")

    def is_finished(self):
        return self._finished

    def kill(self):
        self._finished = True
