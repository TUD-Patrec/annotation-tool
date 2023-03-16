import logging
import os
from typing import Optional

import numpy as np

from .base import MediaReader, register_media_reader


class MocapReader(MediaReader):
    def __init__(self, path: os.PathLike, **kwargs):
        self._mocap = None
        super().__init__(path)

        print(f"{self.fps = }, {self.n_frames = }")

    @property
    def media(self):
        if self._mocap is None:
            self._mocap = self.__read_media__()
        return self._mocap

    def __del__(self):
        pass

    def __get_frame__(self, idx: int) -> np.ndarray:
        """
        Returns the mocap-frame at the given index.
        """
        return self.media.get_frame(idx)

    def __read_media__(self):
        from .mocap_readers import get_mocap_reader

        return get_mocap_reader(self.path)

    def __detect_fps__(self) -> Optional[float]:
        return None

    def __detect_n_frames__(self) -> int:
        return self.media.get_frame_count()


def __is_mocap__(path: os.PathLike) -> bool:
    # TODO improve
    file_extensions = [".c3d", ".bvh", ".csv"]
    return os.path.splitext(path)[1] in file_extensions


def __mocap_builder__(path: os.PathLike, **kwargs) -> MocapReader:
    """
    Builds a MocapReader object from the given path.

    Args:
        path (os.PathLike): The path to the mocap file.
        fps (float): The framerate of the mocap data.

    Returns:
        MocapReader: The MocapReader object.
    """
    return MocapReader(path, **kwargs)


register_media_reader(
    media_type="mocap", selector_function=__is_mocap__, factory=__mocap_builder__
)

logging.debug("MocapReader registered.")
