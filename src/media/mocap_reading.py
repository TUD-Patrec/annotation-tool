import os

import numpy as np

from src.media.media_base import MediaBase
from src.utility.mocap_reader import (
    __calculate_skeleton__,
    body_segments_reversed,
    load_mocap,
)


def centralize_skeleton(skeleton: np.ndarray) -> np.ndarray:
    """
    Centralize the skeleton to stay in the center of the coordinate system.

    Args:
        skeleton (np.ndarray): Skeleton to centralize.

    Returns:
        np.ndarray: Centralized skeleton.
    """
    segments = [
        body_segments_reversed[i] for i in ["L toe", "R toe", "L foot", "R foot"]
    ]
    height = min(skeleton[segment * 2, 2] for segment in segments)
    skeleton[:, 2] -= height
    return skeleton


def normalize_frame(skeleton: np.ndarray) -> np.ndarray:
    """Normalize the skeletons height relative to the ground.

    Args:
        skeleton (np.ndarray): Skeleton to normalize.

    Returns:
        np.ndarray: Normalized skeleton.
    """
    normalizing_vector = skeleton[66:72]  # 66:72 are the columns for lowerback
    return skeleton - np.repeat(normalizing_vector.reshape(1, -1), 22, axis=0).flatten()


class MocapMedia(MediaBase):
    """
    Class for reading mocap data.

    Args:
        path (os.PathLike): The path to the mocap file.
        normalize (bool, optional): Normalize the mocap data. Defaults to False.
    """

    def __init__(self, path: os.PathLike, normalize: bool = False) -> None:
        """
        Initializes a new MocapMedia object.

        Args:
            path (os.PathLike): The path to the mocap file.
            normalize (bool, optional): Normalize the mocap data. Defaults to False.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        super().__init__(path)

        self._data = None
        self._data: np.ndarray = load_mocap(path)
        self._normalize = normalize

    def calculate_skeleton(self, frame: np.ndarray) -> np.ndarray:
        """
        Calculate the skeleton from the given frame.

        Args:
            frame (np.ndarray): Frame to calculate the skeleton from.

        Returns:
            np.ndarray: Skeleton calculated from the given frame.
        """

        if self.normalize:
            frame = normalize_frame(frame)

        skeleton = __calculate_skeleton__(frame)

        skeleton = centralize_skeleton(skeleton)

        return skeleton

    def __get_frame__(self, idx: int) -> np.ndarray:
        """
        Returns the skeleton at the given frame index.

        Args:
            idx (int): Frame index.

        Returns:
            np.ndarray: Skeleton at the given frame index.

        Raises:
            IndexError: If the index is out of range.
        """
        if idx < 0 or idx >= len(self):
            raise IndexError("Index out of range.")
        return self.calculate_skeleton(self.data[idx])
