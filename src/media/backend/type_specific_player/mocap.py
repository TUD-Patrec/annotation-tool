import logging

import PyQt5.QtCore as qtc
import numpy as np
import pyqtgraph.opengl as gl

from src.dataclasses.settings import Settings
from src.media.backend.player import (
    AbstractMediaLoader,
    AbstractMediaPlayer,
    UpdateReason,
)
from src.utility import mocap_reader


class MocapLoader(AbstractMediaLoader):
    def __init__(self, path) -> None:
        super().__init__(path)

    def load(self):
        try:
            array = mocap_reader.load_mocap(self.path, normalize=False)

            n = array.shape[0]

            # Calculate Skeleton
            frames = np.zeros((n, 44, 3))  # dimensions are( frames, bodysegments, xyz)
            for frame_index in range(n):
                prog = (100 * frame_index) // n
                self.progress.emit(prog)
                frame = array[frame_index, :]
                frame = calculate_skeleton(frame)

                # NORMALIZATION
                height = 0
                for segment in [
                    body_segments_reversed[i]
                    for i in ["L toe", "R toe", "L foot", "R foot"]
                ]:
                    segment_height = frame[segment * 2, 2]
                    height = min((height, segment_height))
                frame[:, 2] -= height
                # END NORMALIZATION

                frames[frame_index, :, :] = frame

            self.media = frames.astype(np.float32)

        except Exception as e:
            raise e


class MocapPlayer(AbstractMediaPlayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.media_backend = MocapBackend()
        self.allow_frame_merges = True
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
        self.n_frames = media.shape[0]
        self.fps = Settings.instance().refresh_rate

        logging.info(f"{media.dtype = }, {media.nbytes = }")

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
        self.current_skeleton.setData(
            pos=skeleton, color=np.array(skeleton_colors), width=4, mode="lines"
        )

    def mousePressEvent(self, ev):
        lpos = ev.position() if hasattr(ev, "position") else ev.localPos()
        self.mousePos = lpos
        if ev.button() == qtc.Qt.RightButton:
            self.right_mouse_btn_clicked.emit()


body_segments = {
    -1: "none",
    0: "head",
    1: "head end",
    2: "L collar",
    12: "R collar",
    6: "L humerus",
    16: "R humerus",
    3: "L elbow",
    13: "R elbow",
    9: "L wrist",
    19: "R wrist",
    10: "L wrist end",
    20: "R wrist end",
    11: "lower back",
    21: "root",
    4: "L femur",
    14: "R femur",
    7: "L tibia",
    17: "R tibia",
    5: "L foot",
    15: "R foot",
    8: "L toe",
    18: "R toe",
}

body_segments_reversed = {v: k for k, v in body_segments.items()}

colors = {"r": (1, 0, 0, 1), "g": (0, 1, 0, 1), "b": (0, 0, 1, 1), "y": (1, 1, 0, 1)}

# each bodysegmentline needs 2 colors because each has a start and end.
# different colors on each end result in a gradient
skeleton_colors = (
    colors["b"],
    colors["b"],  # head
    colors["b"],
    colors["b"],  # head end
    colors["b"],
    colors["b"],  # L collar
    colors["g"],
    colors["g"],  # L elbow
    colors["r"],
    colors["r"],  # L femur
    colors["r"],
    colors["r"],  # L foot
    colors["g"],
    colors["g"],  # L humerus
    colors["r"],
    colors["r"],  # L tibia
    colors["r"],
    colors["r"],  # L toe
    colors["g"],
    colors["g"],  # L wrist
    colors["g"],
    colors["g"],  # L wrist end
    colors["b"],
    colors["b"],  # lower back
    colors["b"],
    colors["b"],  # R collar
    colors["g"],
    colors["g"],  # R elbow
    colors["r"],
    colors["r"],  # R femur
    colors["r"],
    colors["r"],  # R foot
    colors["g"],
    colors["g"],  # R humerus
    colors["r"],
    colors["r"],  # R tibia
    colors["r"],
    colors["r"],  # R toe
    colors["g"],
    colors["g"],  # R wrist
    colors["g"],
    colors["g"],  # R wrist end
    colors["b"],
    colors["b"],  # root
)


def calculate_skeleton(frame: np.array) -> np.array:
    """Calculates the lines indicating positions of bodysegments at a single timestep

    Arguments:
    ---------
    frame_index : int
        an integer between 0 and self.number_samples
        denotes the frame/timestep at which the skeleton should be calculated
    ---------

    Returns:
    ---------
    array : numpy.array
        2D array with shape (44,3).
        Contains 44 3-Tupels or 3D coordinates.
        Each bodysegment gets 2 coordinates, for a start and  an end point.
        There are 22 bodysegments.
    ---------

    """

    # Extraction of Translational data for each bodysegment (source)
    tx = []
    ty = []
    tz = []
    for i in range(22):
        tx.append(frame[i * 6 + 3])
        ty.append(frame[i * 6 + 4])
        tz.append(frame[i * 6 + 5])

    # Extraction of Translational data for each bodysegment (target)
    tu = []  # corresponds to x coordinates
    tv = []  # corresponds to y coordinates
    tw = []  # corresponds to z coordinates
    offset = 3
    for coords in [tu, tv, tw]:  # xyz        ->     uvw
        coords.append(frame[2 * 6 + offset])  # 0   head      -> l collar/rcollar
        coords.append(frame[0 * 6 + offset])  # 1   head end  -> head
        coords.append(frame[11 * 6 + offset])  # 2 l collar    -> lowerback
        coords.append(frame[6 * 6 + offset])  # 3 l elbow     -> l humerus
        coords.append(frame[21 * 6 + offset])  # 4 l femur     -> root
        coords.append(frame[7 * 6 + offset])  # 5 l foot      -> l tibia
        coords.append(frame[2 * 6 + offset])  # 6 l humerus   -> l collar
        coords.append(frame[4 * 6 + offset])  # 7 l tibia     -> l femur
        coords.append(frame[5 * 6 + offset])  # 8 l toe       -> l foot
        coords.append(frame[3 * 6 + offset])  # 9 l wrist     -> l elbow
        coords.append(frame[9 * 6 + offset])  # 10 l wrist end -> l wrist
        coords.append(frame[11 * 6 + offset])  # 11   lowerback -> lowerback
        coords.append(frame[11 * 6 + offset])  # 12 r collar    -> lowerback
        coords.append(frame[16 * 6 + offset])  # 13 r elbow     -> r humerus
        coords.append(frame[21 * 6 + offset])  # 14 r femur     -> root
        coords.append(frame[17 * 6 + offset])  # 15 r foot      -> r tibia
        coords.append(frame[12 * 6 + offset])  # 16 r humerus   -> r collar
        coords.append(frame[14 * 6 + offset])  # 17 r tibia     -> r femur
        coords.append(frame[15 * 6 + offset])  # 18 r toe       -> r foot
        coords.append(frame[13 * 6 + offset])  # 19 r wrist     -> r elbow
        coords.append(frame[19 * 6 + offset])  # 20 r wrist end -> r wrist
        coords.append(frame[11 * 6 + offset])  # 21   root      -> lowerback
        offset += 1

    # combine the 3 lists of source coordinates into a 3-tupel list
    txyz = list(zip(tx, ty, tz))
    # combine the 3 lists of target coordinates into a 3-tupel list
    tuvw = list(zip(tu, tv, tw))
    # append the coordinates from source and target alternatingly to a single list
    t_all = []
    for a, b in zip(txyz, tuvw):
        t_all.append(a)
        t_all.append(b)

    # convert the list into an array,
    # convert millimeters to meters and return the result
    return np.array(t_all) / 1000
