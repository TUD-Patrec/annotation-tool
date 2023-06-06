import logging

import PyQt6.QtWidgets as qtw
import numpy as np
import pyqtgraph.opengl as gl

from annotation_tool.media.backend.player import AbstractMediaPlayer
from annotation_tool.media_reader import media_reader as mr


class MocapPlayer(AbstractMediaPlayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setLayout(qtw.QHBoxLayout())
        self.media = None

        self.graph = gl.GLViewWidget()
        # allow only mouse events
        self.graph.keyPressEvent = lambda event: None
        self.graph.keyReleaseEvent = lambda event: None

        self.zgrid = gl.GLGridItem()

        self.graph.addItem(self.zgrid)

        self.current_skeleton = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, 0]]),
            color=np.array([[0, 0, 0, 0], [0, 0, 0, 0]]),
            mode="lines",
        )
        self.graph.addItem(self.current_skeleton)
        self.layout().addWidget(self.graph)

    def get_skeleton(self, idx):
        array = self.media[idx]
        skeleton = _calculate_skeleton(array)
        skeleton = _fix_skeleton_height(skeleton)
        return skeleton

    def load(self, path):
        self.media = mr(path, normalize=True)
        self.n_frames = len(self.media)
        self.fps = self.media.fps
        self.update_media_position()
        self.loaded.emit(self)

    def update_media_position(self):
        pos = self.position + self.offset
        pos_adjusted = max(0, min(pos, self.n_frames - 1))
        if self.media is not None:
            skeleton = self.get_skeleton(pos_adjusted)
            self.current_skeleton.setData(
                pos=skeleton, color=np.array(_skeleton_colors), width=4, mode="lines"
            )

    def shutdown(self):
        self.setFixedSize(0, 0)
        self.hide()
        self.media = None
        self.terminated = True
        self.finished.emit(self)
        logging.debug("MocapPlayer shutdown")


def _fix_skeleton_height(skeleton: np.ndarray) -> np.ndarray:
    """
    Centralize the skeleton to stay in the center of the coordinate system.

    Args:
        skeleton (np.ndarray): Skeleton to centralize.

    Returns:
        np.ndarray: Centralized skeleton.
    """
    segments = [
        _body_segments_reversed[i] for i in ["L toe", "R toe", "L foot", "R foot"]
    ]
    height = min(skeleton[segment * 2, 2] for segment in segments)
    skeleton[:, 2] -= height
    return skeleton


_body_segments = {
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

_body_segments_reversed = {v: k for k, v in _body_segments.items()}

_colors = {"r": (1, 0, 0, 1), "g": (0, 1, 0, 1), "b": (0, 0, 1, 1), "y": (1, 1, 0, 1)}

# each bodysegmentline needs 2 _colors because each has a start and end.
# different _colors on each end result in a gradient
_skeleton_colors = (
    _colors["b"],
    _colors["b"],  # head
    _colors["b"],
    _colors["b"],  # head end
    _colors["b"],
    _colors["b"],  # L collar
    _colors["g"],
    _colors["g"],  # L elbow
    _colors["r"],
    _colors["r"],  # L femur
    _colors["r"],
    _colors["r"],  # L foot
    _colors["g"],
    _colors["g"],  # L humerus
    _colors["r"],
    _colors["r"],  # L tibia
    _colors["r"],
    _colors["r"],  # L toe
    _colors["g"],
    _colors["g"],  # L wrist
    _colors["g"],
    _colors["g"],  # L wrist end
    _colors["b"],
    _colors["b"],  # lower back
    _colors["b"],
    _colors["b"],  # R collar
    _colors["g"],
    _colors["g"],  # R elbow
    _colors["r"],
    _colors["r"],  # R femur
    _colors["r"],
    _colors["r"],  # R foot
    _colors["g"],
    _colors["g"],  # R humerus
    _colors["r"],
    _colors["r"],  # R tibia
    _colors["r"],
    _colors["r"],  # R toe
    _colors["g"],
    _colors["g"],  # R wrist
    _colors["g"],
    _colors["g"],  # R wrist end
    _colors["b"],
    _colors["b"],  # root
)


def _calculate_skeleton(frame: np.array) -> np.array:
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

    # convert the list into an array, convert mm to meters and return the result
    return np.array(t_all) / 1000
