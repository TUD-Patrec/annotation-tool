import logging
import os
from typing import Optional

import filetype
import numpy as np

from .base import MediaReader, register_media_reader


class VideoReader(MediaReader):
    def __get_frame__(self, idx: int) -> np.ndarray:
        """
        Returns the RGB-frame at the given index.
        """
        return self.media.get_frame(idx)

    def __read_media__(self):
        from .video_readers import get_video_reader

        return get_video_reader(self.path)

    def __detect_fps__(self) -> Optional[float]:
        return self.media.get_fps()

    def __detect_n_frames__(self) -> int:
        return self.media.get_frame_count()


def __is_video__(path: os.PathLike) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        return filetype.is_video(path)
    except TypeError:
        return False


def __video_builder__(path=None, **kwargs) -> VideoReader:
    if __is_video__(path):
        return VideoReader(path, **kwargs)
    else:
        raise ValueError(f"Path {path} is not a video.")


register_media_reader(
    media_type="video_readers",
    selector_function=__is_video__,
    factory=__video_builder__,
)

logging.debug("VideoReader registered.")
