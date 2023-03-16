import logging
import os
from typing import Optional

import cv2
import filetype
import numpy as np
from torchvision.io import VideoReader as TorchVideoReader

from .base import MediaReader, register_media_reader


def __get_vc__(path: os.PathLike) -> cv2.VideoCapture:
    """
    Returns a cv2.VideoCapture object for the given path.

    Args:
        path (os.PathLike): The path to the video file.

    Returns:
        cv2.VideoCapture: The cv2.VideoCapture object.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read as video.
    """
    try:
        _vc = cv2.VideoCapture(path)
    except Exception:
        raise IOError("Loading video failed.")

    frame_count = int(_vc.get(cv2.CAP_PROP_FRAME_COUNT))

    if frame_count > 0:
        ok, _ = _vc.read()  # test if video is readable
        if not ok:
            raise IOError(f"Reading single frame from {path} failed.")
    else:
        raise IOError(f"Video at {path} has no frames.")

    _vc.set(cv2.CAP_PROP_POS_FRAMES, 0)  # reset to first frame

    return _vc


def __is_video__(path: os.PathLike) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        first_check = filetype.is_video(path)
    except TypeError:
        return False

    if first_check:
        try:
            __get_vc__(path)  # check if cv can read the file
            return True  # cv can read the file
        except Exception:
            return False
    else:
        return False


class VideoReader(MediaReader):
    """Class for reading video data."""

    def __init__(self, path, **kwargs) -> None:
        super().__init__(path, **kwargs)

        self._pos = 0

        self._delay_tolerance = 10  # frames

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __iter__(self):
        return self[:]

    def __get_frame__(self, idx: int) -> np.ndarray:
        if idx < 0 or idx >= len(self):
            raise IndexError("Index out of range.")

        is_next_frame = idx == self._pos + 1
        if not is_next_frame:
            self._seek(idx)

        self._pos = idx

        x = next(self.media)["data"].numpy()
        x = x.transpose(1, 2, 0)
        return x

    def __read_media__(self):
        __vr = TorchVideoReader(self.path)
        return __vr

    def __detect_fps__(self) -> Optional[float]:
        return self.media.get_metadata().get("video").get("fps")[0]

    def __detect_n_frames__(self) -> int:
        return int(self.media.get_metadata().get("video").get("duration")[0] * self.fps)

    @property
    def current_position(self):
        return self._pos

    def _seek(self, idx: int) -> None:
        print("seeking to", idx)
        time_stamp = idx / self.fps
        self.media.seek(time_stamp)

    def close(self):
        self.__del__()


def __video_builder__(path=None, **kwargs) -> VideoReader:
    if __is_video__(path):
        return VideoReader(path, **kwargs)
    else:
        raise IOError(f"{path} is not a video file.")


register_media_reader(
    media_type="video_2", selector_function=__is_video__, factory=__video_builder__
)

logging.debug("VideoReader registered.")

print("VideoReader TORCH registered.")
