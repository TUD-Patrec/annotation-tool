import abc
import os
from typing import Optional

import numpy as np


class MediaBase:
    """
    Baseclass for media readers (e.g. video, mocap, etc.)
    """

    def __init__(self, path: os.PathLike) -> None:
        """
        Initializes a new MediaBase object.

        Args:
            path: The path to the media file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        import src.utility.filehandler as filehandler

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
        import src.utility.filehandler as filehandler

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
    def duration(self) -> Optional[float]:
        """
        Returns the duration of the media in seconds.
        """
        if self.n_frames is None or self.fps is None:
            return None
        return self.n_frames / self.fps

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def n_frames(self) -> int:
        return self._n_frames

    def __len__(self):
        return self.n_frames

    def __eq__(self, other) -> bool:
        if isinstance(other, MediaBase):
            return self.id == other.id
        return False

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
