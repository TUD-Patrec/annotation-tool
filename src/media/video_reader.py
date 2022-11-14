import logging
import os

import cv2
import numpy as np

from src.media.media_base import MediaBase


class VideoReader(MediaBase):
    def __init__(self, path: os.PathLike) -> None:
        super().__init__(path)

        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} not found.")
        self._vc = cv2.VideoCapture(path)

        ok, frame = self._vc.read()  # read frame to get number of channels
        if ok:
            self._frame_channels = int(frame.shape[-1])
        else:
            raise IOError(f"cannot read frame from {self._filename}.")

        self._seek(0)  # reset to first frame

        self._n_frames = int(self._vc.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = self._vc.get(cv2.CAP_PROP_FPS)

    def __del__(self):
        try:
            self._vc.release()
        except AttributeError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __iter__(self):
        return self[:]

    def __get_frame__(self, idx: int) -> np.ndarray:
        if idx < 0 or idx >= len(self):
            raise IndexError("Index out of range.")

        is_current_frame = idx == self.current_position
        if not is_current_frame:
            self._seek(idx)

        ok, frame = self._vc.read()
        if ok:
            return frame
        else:
            logging.error(f"cannot read frame {idx} from {self._filename}.")
            return None

    @property
    def current_position(self):
        return int(self._vc.get(cv2.CAP_PROP_POS_FRAMES))

    @property
    def width(self):
        return int(self._vc.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self._vc.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def frame_format(self):
        return self._vc.get(cv2.CAP_PROP_FORMAT)

    @property
    def frame_channels(self):
        return self._frame_channels

    def _seek(self, idx: int) -> None:
        self._vc.set(cv2.CAP_PROP_POS_FRAMES, idx)

    def close(self):
        self.__del__()
