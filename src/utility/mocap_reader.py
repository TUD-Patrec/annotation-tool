import logging
import os

import numpy as np

from src.media.media_types import MediaType, media_type_of
from src.utility import filehandler


def load_mocap(path: os.PathLike, normalize=False) -> np.ndarray:
    """Load Motion-capture data from file to numpy array.

    Args:
        path (os.PathLike): Path to motion-capture data.
        normalize (bool, optional): Normalize the Skeleton to stay in
        the center of the coordinate system. Defaults to False.

    Raises:
        RuntimeError: If loading mocap failed even if media-type is correct.
        TypeError: Wrong media-type

    Returns:
        np.ndarray: Array containing the loaded motion-capture data.
    """
    if media_type_of(path) == MediaType.LARA_MOCAP:
        try:
            return __load_lara_mocap__(path, normalize)
        except Exception:
            raise RuntimeError(f"Reading mocap-data from {path} failed.")
    else:
        raise TypeError


def __load_lara_mocap__(path: os.PathLike, normalize: bool) -> np.ndarray:
    try:
        array = filehandler.read_csv(path)
        array = array[:, 2:]
        logging.info(f"{normalize = }")
        if normalize:
            normalizing_vector = array[:, 66:72]  # 66:72 are the columns for lowerback
            for _ in range(21):
                normalizing_vector = np.hstack((normalizing_vector, array[:, 66:72]))
            array = np.subtract(array, normalizing_vector)
        return array
    except Exception as e:
        raise e


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

    # convert the list into an array, convert mm to meters and return the result
    return np.array(t_all) / 1000
