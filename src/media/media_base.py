import abc
import os
from typing import Optional, Union

import cv2 as cv
import numpy as np

import src.utility.filehandler as filehandler


class MediaReader:
    """
    Baseclass for media readers (e.g. video, mocap, etc.)
    """

    def __init__(self, path: os.PathLike) -> None:
        """
        Initializes a new MediaReader object.

        Args:
            path: The path to the media file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        self._path = path
        self._id = filehandler.footprint_of_file(path)
        self._n_frames = None
        self._fps = None

    @property
    def path(self) -> os.PathLike:
        return self._path

    @path.setter
    def path(self, value: os.PathLike) -> None:
        """
        Sets the path of the media file.

        Args:
            value: The new path.
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file has changed.
        """

        if not os.path.isfile(value):
            raise FileNotFoundError(value)
        if self.id != filehandler.footprint_of_file(value):
            raise ValueError("The file has changed")
        self._path = value

    @property
    def id(self) -> str:
        return self._id

    @property
    def footprint(self) -> str:
        return self.id

    @property
    def duration(self) -> Optional[int]:
        """
        Returns the duration of the media in milliseconds.
        """
        if self.n_frames is None or self.fps is None:
            return None
        return int(self.n_frames / self.fps) * 1000

    @property
    def fps(self) -> float:
        if self._fps:
            return self._fps
        else:
            from src.settings import settings

            return settings.refresh_rate

    @property
    def n_frames(self) -> int:
        return self._n_frames

    def __len__(self):
        return self.n_frames

    def __eq__(self, other) -> bool:
        if isinstance(other, MediaReader):
            return self.id == other.id
        return False

    def __del__(self):
        memoizer.remove(self)

    def __getitem__(self, idx):
        """
        Returns the frame at the given index.
        If the index is a slice, returns a list of frames.

        Args:
            idx: The index/indices of the frame(s) to return.
        Returns:
            The frame(s) at the given indices.
        Raises:
            IndexError: If the index is out of range.
            TypeError: If the index/indices are not integers.
        """

        if isinstance(idx, slice):
            return (self[i] for i in range(*idx.indices(len(self))))
        elif isinstance(list, tuple):
            return (self[i] for i in idx)
        elif isinstance(idx, int):
            if idx >= len(self):
                raise IndexError("Index out of range.")
            return self.__get_frame__(idx)
        else:
            raise TypeError("Invalid argument type.")

    @abc.abstractmethod
    def __get_frame__(self, idx: int) -> np.ndarray:
        """
        Returns the frame at the given index.

        Args:
            idx: The index of the frame to return.
        Returns:
            The frame at the given index.
        """
        raise NotImplementedError

    @property
    def media(self):
        """
        We need to make sure that this is not stored in the class, because it
        cannot be pickled.
        """
        return memoizer(self)


class Memoizer:
    def __init__(self):
        self._cache = []

    def __call__(self, mr: MediaReader) -> Union[cv.VideoCapture, np.ndarray]:
        """
        Returns the memorized version of the given MediaReader.

        Args:
            mr: The MediaReader to memorize.

        Returns:
            The memorized version of the MediaReader.
        """
        # check if vr already registered
        for (reader, memorized_vr) in self._cache:
            if reader is mr:
                return memorized_vr
        else:
            from .mocap_reader import MocapReader, get_mocap
            from .video_reader import VideoReader, get_cv

            if isinstance(mr, VideoReader):
                memorized_vr = get_cv(mr.path)
            elif isinstance(mr, MocapReader):
                memorized_vr = np.copy(get_mocap(mr.path))
            else:
                raise TypeError("Invalid MediaReader type.")
            self._cache.append((mr, memorized_vr))

            return memorized_vr

    def remove(self, mr: MediaReader) -> None:
        """
        Removes the given MediaReader from the cache.

        Args:
            mr: The MediaReader to remove.
        """
        for (reader, memorized_vr) in self._cache:
            if reader is mr:
                self._cache.remove((reader, memorized_vr))

                if isinstance(memorized_vr, cv.VideoCapture):
                    memorized_vr.release()
                    print("Released VideoCapture object.")
                break


memoizer = Memoizer()
