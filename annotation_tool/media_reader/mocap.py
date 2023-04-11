import logging
import os
from typing import Optional, Union

import numpy as np

from .base import MediaReader, register_media_reader


class MocapReader(MediaReader):
    def __init__(self, path: os.PathLike, **kwargs) -> None:
        super().__init__(path, **kwargs)

        from .mocap_readers import get_mocap_reader

        try:
            self._mocap_reader = get_mocap_reader(path)
        except ValueError as e:
            raise ValueError(f"Could not load mocap data {path}.") from e

        self._fps = kwargs.get("fps", None)
        self._duration = kwargs.get("duration", None)

    def __get_frame__(self, idx: int) -> np.ndarray:
        return self._mocap_reader.get_frame(idx)

    def __get_frame_count__(self) -> int:
        return self._mocap_reader.get_frame_count()

    def __get_duration__(self) -> Optional[float]:
        if self._duration is None:
            self._duration = self._mocap_reader.get_duration()
        return self._duration

    def __get_fps__(self) -> Optional[float]:
        if self._fps is None:
            self._fps = self._mocap_reader.get_fps()
        return self._fps

    def __get_path__(self) -> os.PathLike:
        return self._mocap_reader.get_path()

    def __set_fps__(self, fps: Union[int, float]) -> None:
        if not isinstance(fps, (int, float)):
            raise TypeError("Framerate must be a number.")
        if fps <= 0:
            raise ValueError("Framerate must be positive.")
        self._fps = fps


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
