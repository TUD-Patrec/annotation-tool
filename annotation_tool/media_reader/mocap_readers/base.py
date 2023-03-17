import abc
import dataclasses
import logging
import os
from typing import Optional

import numpy as np


class MocapReaderBase(abc.ABC):
    """
    Abstract class for video_readers readers.
    """

    @abc.abstractmethod
    def __init__(self, path: os.PathLike, **kwargs):
        """
        Initializes the video_readers reader.

        Args:
            path (os.PathLike): The path to the video_readers file.
        """
        pass

    @abc.abstractmethod
    def get_frame(self, frame_idx: int) -> np.ndarray:
        """
        Returns the RGB-frame at the given index.

        Args:
            frame_idx (int): The index of the frame.

        Returns:
            np.ndarray: The frame as a numpy array. The shape is (height, width, channels).
                The channels are in RGB order.
        Raises:
            IndexError: If the frame index is out of bounds.
        """
        pass

    @abc.abstractmethod
    def get_frame_count(self) -> int:
        """
        Returns the number of frames in the video_readers.

        Returns:
            int: The number of frames.
        """
        pass

    @abc.abstractmethod
    def get_fps(self) -> Optional[float]:
        """
        Returns the frames per second of the video_readers.

        Returns:
            Optional[float]: The frames per second. None if the video_readers has no fps.
        """
        pass

    @abc.abstractmethod
    def get_duration(self) -> Optional[float]:
        """
        Returns the duration of the video_readers in seconds.

        Returns:
            float: The duration of the video_readers in seconds. None if the video_readers has no duration.
        """
        pass

    @abc.abstractmethod
    def get_path(self) -> os.PathLike:
        """
        Returns the path to the video_readers.
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def is_supported(path: os.PathLike) -> bool:
        """
        Returns whether the video_readers format is supported by the reader.

        Args:
            path (os.PathLike): The path to the video_readers file.

        Returns:
            bool: Whether the video_readers format is supported by the reader.
        """
        return False


class __Memoizer:
    def __init__(self):
        self._cache = {}

    def __call__(self, mr: MocapReaderBase) -> np.ndarray:
        """
        Returns the memorized version of the given __MediaReader.

        Args:
            mr: The __MediaReader to memorize.

        Returns:
            The memorized version of the __MediaReader.
        """
        if not isinstance(mr, MocapReaderBase):
            raise TypeError("Invalid argument type.")
        key = id(mr)
        if key not in self._cache:
            media = mr.__read_media__()
            self._cache[key] = media

        return self._cache[key]

    def remove(self, mr: MocapReaderBase) -> None:
        """
        Removes the given __MediaReader from the cache.

        Args:
            mr: The __MediaReader to remove.
        """
        key = id(mr)
        if key in self._cache:
            del self._cache[key]
            logging.debug(f"Removed {mr} from cache. Cache size: {len(self._cache)}")


@dataclasses.dataclass
class RegisteredMocapReader:
    """
    Dataclass for registered video_readers readers.
    """

    reader: MocapReaderBase
    priority: int


__registered_mocap_readers = []


def register_mocap_reader(reader: MocapReaderBase, priority: int = 0):
    """
    Registers a video_readers reader.

    Args:
        reader (VideoReaderBase): The video_readers reader to register.
        priority (int, optional): The priority of the reader. Defaults to 0.
    """
    __registered_mocap_readers.append(RegisteredMocapReader(reader, priority))
    __registered_mocap_readers.sort(key=lambda x: x.priority, reverse=True)


def get_mocap_reader(path: os.PathLike) -> MocapReaderBase:
    for reader in __registered_mocap_readers:
        if reader.reader.is_supported(path):
            return reader.reader(path)
    raise ValueError(f"No video_readers reader found for {path}.")
