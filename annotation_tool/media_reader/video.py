import logging
from pathlib import Path
from typing import Optional

import filetype
import numpy as np

from .base import MediaReader, register_media_reader


class VideoReader(MediaReader):
    """
    Adapter class for video_readers for loading and reading videos frame by frame.
    """

    def __init__(self, path: Path, **kwargs) -> None:
        super().__init__(path, **kwargs)

        from .video_readers import get_video_reader

        try:
            self._video_reader = get_video_reader(path)
        except ValueError as e:
            raise ValueError(f"Could not load video {path}.") from e

    def __get_frame__(self, idx: int) -> np.ndarray:
        return self._video_reader.get_frame(idx)

    def __get_frame_count__(self) -> int:
        return self._video_reader.get_frame_count()

    def __get_fps__(self) -> Optional[float]:
        return self._video_reader.get_fps()

    def __get_path__(self) -> Path:
        return self._video_reader.get_path()


def __is_video__(path: Path) -> bool:
    if path.is_file():
        try:
            return filetype.is_video(path)
        except TypeError:
            return False
    else:
        raise FileNotFoundError(f"File {path} does not exist.")


def __video_builder__(path, **kwargs) -> VideoReader:
    if __is_video__(path):
        return VideoReader(path, **kwargs)
    else:
        raise ValueError(f"Path {path} is not a video.")


register_media_reader(
    media_type="video",
    selector_function=__is_video__,
    factory=__video_builder__,
)

logging.debug("VideoReader registered.")
