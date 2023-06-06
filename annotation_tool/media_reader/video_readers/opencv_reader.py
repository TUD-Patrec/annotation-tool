from functools import lru_cache
import logging
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from .base import VideoReaderBase


def __get_vc__(path: Path) -> cv2.VideoCapture:
    """
    Returns a cv2.VideoCapture object for the given path.

    Args:
        path (Path): The path to the video_readers file.

    Returns:
        cv2.VideoCapture: The cv2.VideoCapture object.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read as video_readers.
    """
    try:
        _vc = cv2.VideoCapture(path.as_posix())
    except Exception:
        raise IOError("Loading video_readers failed.")

    frame_count = int(_vc.get(cv2.CAP_PROP_FRAME_COUNT))

    if frame_count > 0:
        ok, _ = _vc.read()  # test if video_readers is readable
        if not ok:
            raise IOError(f"Reading single frame from {path} failed.")
    else:
        raise IOError(f"Video at {path} has no frames.")

    _vc.set(cv2.CAP_PROP_POS_FRAMES, 0)  # reset to first frame

    return _vc


class OpenCvReader(VideoReaderBase):
    def __init__(self, path: Path, **kwargs):
        self.path = path
        self.media = __get_vc__(path)

        self.FAST_SEEK_THRESHOLD = 7  # number of frames to skip instead of seeking

        logging.info(f"Using OpenCV for video {path}.")

    def get_frame(self, frame_idx: int) -> np.ndarray:
        if frame_idx < 0 or frame_idx >= self.get_frame_count():
            raise IndexError("Index out of range.")

        try:
            self._seek(frame_idx)
        except AssertionError as e:
            print(repr(e))
            logging.error(f"Seeking to frame {frame_idx} failed.")
            return np.zeros((self.get_height(), self.get_width(), 3), dtype=np.uint8)

        ok, frame = self.media.read()
        if ok:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            logging.error(f"Reading frame {frame_idx} failed.")
            return np.zeros((self.get_height(), self.get_width(), 3), dtype=np.uint8)

    @property
    def current_position(self):
        return int(self.media.get(cv2.CAP_PROP_POS_FRAMES))

    def _seek(self, idx: int) -> None:

        pos = self.current_position

        if idx == pos:
            return

        backward_seek = idx < pos

        delta = abs(idx - pos)
        distant_forward_seek = delta > self.FAST_SEEK_THRESHOLD

        if backward_seek or distant_forward_seek:
            self._set_cap_pos(idx)
        else:
            self._skip_frames(idx - self.current_position)

        assert (
            self.current_position == idx
        ), f"Seeking failed. Expected index {idx}, got {self.current_position}."  # sanity check

    def _set_cap_pos(self, idx: int) -> None:
        self.media.set(cv2.CAP_PROP_POS_FRAMES, idx)

    def _skip_frames(self, frames_to_skip) -> None:
        for _ in range(frames_to_skip):
            self.media.read()

    @lru_cache(maxsize=1)
    def get_frame_count(self) -> int:
        return int(self.media.get(cv2.CAP_PROP_FRAME_COUNT))

    @lru_cache(maxsize=1)
    def get_fps(self) -> float:
        return self.media.get(cv2.CAP_PROP_FPS)

    @lru_cache(maxsize=1)
    def get_height(self) -> int:
        return int(self.media.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @lru_cache(maxsize=1)
    def get_width(self) -> int:
        return int(self.media.get(cv2.CAP_PROP_FRAME_WIDTH))

    def get_size(self) -> Tuple[int, int]:
        return self.get_width(), self.get_height()

    def get_path(self) -> Path:
        return self.path

    @staticmethod
    def is_supported(path: Path) -> bool:
        try:
            _vc = cv2.VideoCapture(path.as_posix())
        except Exception as e:  # noqa
            return False

        if int(_vc.get(cv2.CAP_PROP_FRAME_COUNT)) > 0:
            ok, _ = _vc.read()  # test if video_readers is readable
            if not ok:
                return False
        else:
            return False

        _vc.release()
        return True


from .base import register_video_reader

register_video_reader(OpenCvReader, 0)
logging.info("Registered OpenCvReader.")
