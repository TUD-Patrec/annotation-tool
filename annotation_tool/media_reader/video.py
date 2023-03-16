import logging
import os
import time
from typing import Optional

import cv2
import filetype
import numpy as np

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


class RingBufEval:
    def __init__(self, n):
        self._arr = np.array([0.1] * n, dtype=float)  # 0.1 is reasonable default
        self._idx = 0

    def push(self, x):
        self._arr[self._idx] = x
        self._idx = (self._idx + 1) % len(self._arr)

    def mean(self):
        return np.mean(self._arr)


class VideoReader(MediaReader):
    """Class for reading video data."""

    def __init__(self, path, **kwargs) -> None:
        super().__init__(path, **kwargs)
        self.FAST_SEEK_THRESHOLD = 10
        self.MIN_SEEK_THRESHOLD = 5
        self.MAX_SEEK_THRESHOLD = 15
        self._EVAL_INTERVAL = 5  # seconds
        self._MIN_PERCENT = 0.75

        buf_size = 10
        self.slow_eval_buf = RingBufEval(buf_size)
        self.fast_eval_buf = RingBufEval(buf_size)
        self.delta_eval_buf = RingBufEval(buf_size)

        self._last_eval_time = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __iter__(self):
        return self[:]

    def __get_frame__(self, idx: int) -> np.ndarray:
        if idx < 0 or idx >= len(self):
            raise IndexError("Index out of range.")

        self._seek(idx)

        ok, frame = self.media.read()
        if ok:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            logging.error(f"cannot read frame {idx} from {self.path}.")
            return None

    def __read_media__(self):
        return __get_vc__(self.path)

    def __detect_fps__(self) -> Optional[float]:
        return self.media.get(cv2.CAP_PROP_FPS)

    def __detect_n_frames__(self) -> int:
        return int(self.media.get(cv2.CAP_PROP_FRAME_COUNT))

    def _eval_performance(self):
        if time.time() - self._last_eval_time > self._EVAL_INTERVAL:
            self._last_eval_time = time.time()

            fast_seek_mean_delta = self.fast_eval_buf.mean()
            slow_seek_mean_delta = self.slow_eval_buf.mean()
            prev_delta_mean = self.delta_eval_buf.mean()

            if fast_seek_mean_delta > slow_seek_mean_delta:
                self.FAST_SEEK_THRESHOLD -= 1
                self.FAST_SEEK_THRESHOLD = max(
                    self.MIN_SEEK_THRESHOLD, self.FAST_SEEK_THRESHOLD
                )

            # only increase if in relevant range: comparing fast_seek with only a few frames to slow_seek otherwise unfair
            elif prev_delta_mean > self._MIN_PERCENT * self.FAST_SEEK_THRESHOLD:
                self.FAST_SEEK_THRESHOLD += 1
                self.FAST_SEEK_THRESHOLD = min(
                    self.MAX_SEEK_THRESHOLD, self.FAST_SEEK_THRESHOLD
                )

            # print(f"slow seek mean: {slow_seek_mean_delta}")
            # print(f"fast seek mean: {fast_seek_mean_delta}")
            # print(f"prev delta mean: {prev_delta_mean}")
            # print(f"FAST_SEEK_THRESHOLD: {self.FAST_SEEK_THRESHOLD}")
            # print()

    @property
    def current_position(self):
        return int(self.media.get(cv2.CAP_PROP_POS_FRAMES))

    def _seek(self, idx: int) -> None:
        self._eval_performance()

        _current_pos = self.current_position

        if idx == _current_pos:
            return

        backward_seek = idx < _current_pos
        delta = abs(idx - _current_pos)
        self.delta_eval_buf.push(delta)
        distant_forward_seek = delta > self.FAST_SEEK_THRESHOLD

        if backward_seek or distant_forward_seek:
            self._slow_seek(idx)
        else:
            self._fast_seek(idx)

        assert self.current_position == idx  # sanity check, kind of expensive

    def _slow_seek(self, idx: int) -> None:
        start = time.perf_counter()
        self.media.set(cv2.CAP_PROP_POS_FRAMES, idx)
        delta = time.perf_counter() - start
        self.slow_eval_buf.push(delta)

    def _fast_seek(self, idx: int) -> None:
        start = time.perf_counter()
        for _ in range(idx - self.current_position):
            self.media.read()
        delta = time.perf_counter() - start
        self.fast_eval_buf.push(delta)

    def close(self):
        self.__del__()


def __video_builder__(path=None, **kwargs) -> VideoReader:
    if __is_video__(path):
        return VideoReader(path, **kwargs)
    else:
        raise IOError(f"{path} is not a video file.")


register_media_reader(
    media_type="video", selector_function=__is_video__, factory=__video_builder__
)

logging.debug("VideoReader registered.")
