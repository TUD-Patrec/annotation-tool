import logging
from pathlib import Path
from typing import Optional

import numpy as np

from .base import MediaReader, register_media_reader


class MocapReader(MediaReader):
    def __init__(self, path: Path, **kwargs) -> None:
        super().__init__(path, **kwargs)

        from .mocap_readers import get_mocap_reader

        try:
            self._mocap_reader = get_mocap_reader(path, **kwargs)
        except ValueError as e:
            raise ValueError(f"Could not load mocap data {path}.") from e

        self._fps = kwargs.get("fps", None)
        self._duration = kwargs.get("duration", None)

    def __get_frame__(self, idx: int) -> np.ndarray:
        return self._mocap_reader.get_frame(idx)

    def __get_frame_count__(self) -> int:
        return self._mocap_reader.get_frame_count()

    def __get_fps__(self) -> Optional[float]:
        if self._fps is None:
            self._fps = self._mocap_reader.get_fps()
        return self._fps

    def __get_path__(self) -> Path:
        return self._mocap_reader.get_path()


def __is_mocap__(path: Path) -> bool:
    # TODO improve
    file_extensions = [".c3d", ".bvh", ".csv"]
    return path.suffix.lower() in file_extensions


def __mocap_builder__(path: Path, **kwargs) -> MocapReader:
    """
    Builds a MocapReader object from the given path.

    Args:
        path (Path): The path to the mocap file.
        fps (float): The framerate of the mocap data.

    Returns:
        MocapReader: The MocapReader object.
    """
    return MocapReader(path, **kwargs)


register_media_reader(
    media_type="mocap", selector_function=__is_mocap__, factory=__mocap_builder__
)

logging.debug("MocapReader registered.")
