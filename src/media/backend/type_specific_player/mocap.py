import logging

import PyQt5.QtCore as qtc
import numpy as np
import pyqtgraph.opengl as gl

from src.media.backend.player import (
    AbstractMediaLoader,
    AbstractMediaPlayer,
    UpdateReason,
)
from src.utility import mocap_reader


class MocapLoader(AbstractMediaLoader):
    def __init__(self, path) -> None:
        super().__init__(path)
        self.media = None

    def load(self):
        try:
            self.media = mocap_reader.get_reader(self.path, normalize=True)
        except Exception as e:
            raise e


class MocapPlayer(AbstractMediaPlayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.media_backend = MocapBackend()
        self.media_backend.right_mouse_btn_clicked.connect(self.open_context_menu)

    def load(self, path):
        self.loading_thread = MocapLoader(path)
        self.loading_thread.progress.connect(self.pbar.setValue)
        self.loading_thread.finished.connect(self._loading_finished)
        self.loading_thread.start()
        logging.info("Loading start")

    @qtc.pyqtSlot(np.ndarray)
    def _loading_finished(self, media):
        assert qtc.QThread.currentThread() is self.thread()
        logging.info("Loading done")
        self.n_frames = len(media)
        self.fps = media.fps

        # logging.info(f"{media.dtype = }, {media.nbytes = }")

        self.media_backend.media = media
        self.media_backend.set_position(0)
        self.layout().replaceWidget(self.pbar, self.media_backend)
        self.pbar.setParent(None)
        del self.pbar

        self.loading_thread.quit()
        self.loading_thread.wait()
        self.loading_thread = None

        self.loaded.emit(self)

    def update_media_position(self, update_reason: UpdateReason):
        pos = self.position + self.offset
        pos_adjusted = max(0, min(pos, self.n_frames - 1))
        self.media_backend.set_position(pos_adjusted)

        self.confirm_update(update_reason)

    def shutdown(self):
        assert qtc.QThread.currentThread() is self.thread()
        if self.loading_thread:
            logging.info("Waiting for loading thread to finish")
            self.loading_thread.quit()
            self.loading_thread.wait()


class MocapBackend(gl.GLViewWidget):
    right_mouse_btn_clicked = qtc.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.media = None
        self.position = None

        self.zgrid = gl.GLGridItem()
        self.addItem(self.zgrid)

        self.current_skeleton = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, 0]]),
            color=np.array([[0, 0, 0, 0], [0, 0, 0, 0]]),
            mode="lines",
        )
        self.addItem(self.current_skeleton)

    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        self.position = new_pos  # update position
        skeleton = self.media[self.position]
        skeleton_colors = self.media.skeleton_colors
        self.current_skeleton.setData(
            pos=skeleton, color=np.array(skeleton_colors), width=4, mode="lines"
        )

    def mousePressEvent(self, ev):
        lpos = ev.position() if hasattr(ev, "position") else ev.localPos()
        self.mousePos = lpos
        if ev.button() == qtc.Qt.RightButton:
            self.right_mouse_btn_clicked.emit()
