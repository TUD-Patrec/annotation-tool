import logging
import time

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw
import cv2
import numpy as np

from .media_player import AbstractMediaPlayer, MediaLoader


class VideoPlayer(AbstractMediaPlayer):
    prepare_update = qtc.pyqtSignal(object, int, int, int, bool)
    prepare_update_2 = qtc.pyqtSignal(np.ndarray, int, int, bool)
    exit_signal = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.lblVid = qtw.QLabel(self)
        self.lblVid.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Ignored)
        self.lblVid.setAlignment(qtc.Qt.AlignCenter)
        self.current_img = None

        self.create_worker()

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

    def update_media_position_old(self, emit_pos):
        cap_pos = int(self.media.get(cv2.CAP_PROP_POS_FRAMES))
        pos = self.position + self.offset
        pos = max(0, min(pos, self.n_frames - 1))

        if 0 <= pos < self.n_frames:
            if pos != cap_pos:
                # cap_pos == new_pos <=> Jump to the next frame, which is exactly what next_frame() does
                # only manually update the cap_pos if we want to jump anywhere else
                self.media.set(cv2.CAP_PROP_POS_FRAMES, pos)
            self.next_frame()
        else:
            if pos < 0 and cap_pos != 1:
                self.media.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.next_frame()
            if pos >= self.n_frames and cap_pos != self.n_frames:
                logging.info("loading last frame as placeholder")
                self.media.set(cv2.CAP_PROP_POS_FRAMES, self.n_frames - 1)
                self.next_frame()
        if emit_pos:
            self.position_changed.emit(pos)

    @qtc.pyqtSlot(bool)
    def update_media_position(self, emit_pos):
        assert qtc.QThread.currentThread() is self.thread()
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
                self.media.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.next_frame()
            if pos >= self.n_frames and cap_pos != self.n_frames:
                logging.info("loading last frame as placeholder")
                self.media.set(cv2.CAP_PROP_POS_FRAMES, self.n_frames - 1)
                self.next_frame()

    def next_frame_debug(self):
        start_ges = time.perf_counter()
        start = time.perf_counter()
        ret, frame = self.media.read()
        end = time.perf_counter()
        logging.info(f"1) {end - start = }")
        if ret:

            start = time.perf_counter()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            end = time.perf_counter()
            logging.info(f"2) {end - start = }")

            start = time.perf_counter()
            h, w, ch = frame.shape
            end = time.perf_counter()
            # logging.info(f'3) {end - start = }')

            start = time.perf_counter()
            bytes_per_line = ch * w
            end = time.perf_counter()
            # logging.info(f'4) {end - start = }')

            start = time.perf_counter()
            self.current_img = qtg.QImage(
                frame, w, h, bytes_per_line, qtg.QImage.Format_RGB888
            )
            end = time.perf_counter()
            logging.info(f"5) {end - start = }")

            start = time.perf_counter()
            img = self.current_img.scaled(
                self.lblVid.width(),
                self.lblVid.height(),
                qtc.Qt.KeepAspectRatio,
                qtc.Qt.SmoothTransformation,
            )
            end = time.perf_counter()
            logging.info(f"6) {end - start = }")

            start = time.perf_counter()
            pix = qtg.QPixmap.fromImage(img)
            end = time.perf_counter()
            # logging.info(f'7) {end - start = }')

            # MUSS IN GUI-THREAD PASSIEREN!
            start = time.perf_counter()
            self.lblVid.setPixmap(pix)
            end = time.perf_counter()
            logging.info(f"8) {end - start = }")
            end_ges = time.perf_counter()

            logging.info(f"GESAMT) {end_ges - start_ges = }")

    def next_frame(self):
        ret, frame = self.media.read()
        if ret:
            self.prepare_update_2.emit(
                frame, self.lblVid.width(), self.lblVid.height(), True
            )
        else:
            raise RuntimeError()

    def update_media_position_2(self, emit_pos):
        logging.info("UPDATE MEDIA POSITION")
        pos = self.position + self.offset
        self.prepare_update.emit(
            self.media, self.lblVid.width(), self.lblVid.height(), pos, emit_pos
        )

    def create_worker(self):
        self.helper_thread = qtc.QThread()
        self.helper = VideoHelper()
        self.helper.moveToThread(self.helper_thread)

        self.helper.finished.connect(self.helper_thread.quit)
        self.helper.finished.connect(self.helper.deleteLater)
        self.helper_thread.finished.connect(self.helper_thread.deleteLater)

        self.prepare_update.connect(self.helper.prepare_update)
        self.prepare_update_2.connect(self.helper.read_frame)
        self.exit_signal.connect(self.helper.stop)
        self.helper.update_ready.connect(self.update_ready)

        self.helper_thread.start()

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

    def resizeEvent(self, event):
        if self.current_img:
            qtw.QWidget.resizeEvent(self, event)
            self.lblVid.resize(event.size())
            img = self.current_img.scaled(
                self.lblVid.size(), qtc.Qt.KeepAspectRatio, qtc.Qt.SmoothTransformation
            )
            pix = qtg.QPixmap.fromImage(img)
            self.lblVid.setPixmap(pix)

    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self.exit_signal.emit()
        return super().closeEvent(a0)


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
