import logging
import time

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw
import cv2
import numpy as np

from .media_player import AbstractMediaPlayer, MediaLoader


class VideoPlayer(AbstractMediaPlayer):
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
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)

    def load(self, path):
        self.loading_thread = VideoLoader(path)
        self.loading_thread.progress.connect(self.pbar.setValue)
        self.loading_thread.finished.connect(self._loading_finished)
        self.loading_thread.start()

    @qtc.pyqtSlot(cv2.VideoCapture)
    def _loading_finished(self, media):
        self.media = media

        self.layout().replaceWidget(self.pbar, self.lblVid)

        self.pbar.setParent(None)
        del self.pbar

        self.fps = self.media.get(cv2.CAP_PROP_FPS)
        self.n_frames = int(self.media.get(cv2.CAP_PROP_FRAME_COUNT))
        self.next_frame()
        width = media.get(cv2.CAP_PROP_FRAME_WIDTH)  # float `width`
        height = media.get(cv2.CAP_PROP_FRAME_HEIGHT)
        logging.info("Video-Shape: {} x {}.".format(width, height))

        self.adjustSize()

        self.loaded.emit(self)

    def update_media_position(self):
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
                logging.info("loading first frame as placeholder")
                self.media.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.next_frame()
            if pos >= self.n_frames and cap_pos != self.n_frames:
                logging.info("loading last frame as placeholder")
                self.media.set(cv2.CAP_PROP_POS_FRAMES, self.n_frames - 1)
                self.next_frame()

    def next_frame(self):
        ret, frame = self.media.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w

            self.current_img = qtg.QImage(
                frame, w, h, bytes_per_line, qtg.QImage.Format_RGB888
            )
            img = self.current_img.scaled(
                self.lblVid.width(),
                self.lblVid.height(),
                qtc.Qt.KeepAspectRatio,
                qtc.Qt.SmoothTransformation,
            )
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)

    def resizeEvent(self, event):
        if self.current_img:
            qtw.QWidget.resizeEvent(self, event)
            self.lblVid.resize(event.size())
            img = self.current_img.scaled(
                self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation
            )
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)

    # not used right now
    @qtc.pyqtSlot(qtg.QImage, qtg.QPixmap, bool)
    def update_ready(self, img, pix, emit_pos):
        assert qtc.QThread.currentThread() is self.thread()
        logging.info("UPDATE READY")
        self.current_img = img
        self.lblVid.setPixmap(pix)

        if self.is_main_replay_widget and emit_pos:
            pos = self.position + self.offset
            assert 0 <= pos < self.n_frames
            self.position_changed.emit(pos)
        self.timeout_done.emit(self)


# Not used right now
class VideoHelper(qtc.QObject):
    update_ready = qtc.pyqtSignal(qtg.QImage, qtg.QPixmap, bool)
    finished = qtc.pyqtSignal()

    @qtc.pyqtSlot(object, int, int, int, bool)
    def prepare_update(self, media, width, height, pos, emit_wanted):
        assert qtc.QThread.currentThread() is self.thread()
        logging.info("PREPARING UPDATE")
        cap_pos = int(media.get(cv2.CAP_PROP_POS_FRAMES))
        n_frames = int(media.get(cv2.CAP_PROP_FRAME_COUNT))

        if 0 <= pos < n_frames:
            if pos != cap_pos:
                # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does
                # only manually update the cap_pos if we want to jump anywhere else
                media.set(cv2.CAP_PROP_POS_FRAMES, pos)
        else:
            if pos < 0 and cap_pos != 1:
                logging.info("loading first frame as placeholder")
                media.set(cv2.CAP_PROP_POS_FRAMES, 0)
            elif pos >= n_frames and cap_pos != n_frames:
                logging.info("loading last frame as placeholder")
                media.set(cv2.CAP_PROP_POS_FRAMES, n_frames - 1)
            else:
                assert emit_wanted is False
                self.update_ready.emit(None, None, False)

        assert 0 <= int(media.get(cv2.CAP_PROP_POS_FRAMES)) < n_frames

        # Loading image and pixmap
        ret, frame = media.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            current_img = qtg.QImage(
                frame, w, h, bytes_per_line, qtg.QImage.Format_RGB888
            )
            img = current_img.scaled(
                width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation
            )
            pix = qtg.QPixmap.fromImage(img)

            self.update_ready.emit(current_img, pix, emit_wanted)
        else:
            raise RuntimeError

    @qtc.pyqtSlot(np.ndarray, int, int, bool)
    def read_frame(self, frame, width, height, emit_wanted):
        assert qtc.QThread.currentThread() is self.thread()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        current_img = qtg.QImage(frame, w, h, bytes_per_line, qtg.QImage.Format_RGB888)
        img = current_img.scaled(
            width, height, qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation
        )
        pix = qtg.QPixmap.fromImage(img)

        self.update_ready.emit(current_img, pix, emit_wanted)

    @qtc.pyqtSlot()
    def stop(self):
        self.finished.emit()


class VideoLoader(MediaLoader):
    def __init__(self, path) -> None:
        super().__init__(path)

    def load(self):
        try:
            self.media = cv2.VideoCapture(self.path)
        except:
            logging.error("Could NOT load the video from {}".format(self.path))
            return
        if self.media.get(cv2.CAP_PROP_FRAME_COUNT) < 1:
            logging.error("EMPTY VIDEO LOADED")
