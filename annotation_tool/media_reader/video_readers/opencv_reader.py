from functools import lru_cache
import logging
import os
import time
from typing import Tuple

import cv2
import numpy as np

try:
    from .base import VideoReaderBase
except ImportError:
    from base import VideoReaderBase


def __get_vc__(path: os.PathLike) -> cv2.VideoCapture:
    """
    Returns a cv2.VideoCapture object for the given path.

    Args:
        path (os.PathLike): The path to the video_readers file.

    Returns:
        cv2.VideoCapture: The cv2.VideoCapture object.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read as video_readers.
    """
    try:
        _vc = cv2.VideoCapture(path)
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


class RingBufEval:
    def __init__(self, n):
        self._arr = np.array([0.1] * n, dtype=float)  # 0.1 is reasonable default
        self._idx = 0

    def push(self, x):
        self._arr[self._idx] = x
        self._idx = (self._idx + 1) % len(self._arr)

    def mean(self):
        return np.mean(self._arr)


class OpenCvReader(VideoReaderBase):
    def __init__(self, path: os.PathLike, **kwargs):
        self.path = path
        self.media = __get_vc__(path)

        self.FAST_SEEK_THRESHOLD = 5

        self.use_dynamic_threshold = kwargs.get("dynamic_threshold", False)
        logging.debug(f"Using dynamic threshold: {self.use_dynamic_threshold}.")

        if self.use_dynamic_threshold:
            self.MIN_SEEK_THRESHOLD = 3
            self.MAX_SEEK_THRESHOLD = 15
            self._EVAL_INTERVAL = 5  # seconds
            self._MIN_PERCENT = 0.75

            buf_size = 10
            self.slow_eval_buf = RingBufEval(buf_size)
            self.fast_eval_buf = RingBufEval(buf_size)
            self.delta_eval_buf = RingBufEval(buf_size)

            self._last_eval_time = time.time()

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

    def _eval_performance(self):
        if not self.use_dynamic_threshold:
            return
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
        if self.use_dynamic_threshold:
            self._eval_performance()

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

        if self.use_dynamic_threshold:
            self.delta_eval_buf.push(delta)

        assert (
            self.current_position == idx
        ), f"Seeking failed. Expected index {idx}, got {self.current_position}."  # sanity check

    def _set_cap_pos(self, idx: int) -> None:
        if self.use_dynamic_threshold:
            start = time.perf_counter()
            self.media.set(cv2.CAP_PROP_POS_FRAMES, idx)
            delta = time.perf_counter() - start
            self.slow_eval_buf.push(delta)
        else:
            self.media.set(cv2.CAP_PROP_POS_FRAMES, idx)

    def _skip_frames(self, frames_to_skip) -> None:
        if self.use_dynamic_threshold:
            start = time.perf_counter()
            for _ in range(frames_to_skip):
                self.media.read()
            delta = time.perf_counter() - start
            self.fast_eval_buf.push(delta)
        else:
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

    @lru_cache(maxsize=1)
    def get_duration(self) -> float:
        return self.get_frame_count() / self.get_fps()

    @lru_cache(maxsize=1)
    def get_fourcc(self) -> str:
        return self.media.get(cv2.CAP_PROP_FOURCC)

    @lru_cache(maxsize=1)
    def get_codec(self) -> str:
        return self.media.get(cv2.CAP_PROP_FOURCC)

    def get_path(self) -> os.PathLike:
        return self.path

    @staticmethod
    def is_supported(path: os.PathLike) -> bool:
        try:
            _vc = cv2.VideoCapture(path)
        except:  # noqa
            return False

        if int(_vc.get(cv2.CAP_PROP_FRAME_COUNT)) > 0:
            ok, _ = _vc.read()  # test if video_readers is readable
            if not ok:
                return False
        else:
            return False

        _vc.release()
        return True


try:
    from .base import register_video_reader
except ImportError:
    from base import register_video_reader


register_video_reader(OpenCvReader, 0)
logging.info("Registered OpenCvReader.")
