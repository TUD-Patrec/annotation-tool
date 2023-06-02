import abc
import dataclasses
from pathlib import Path

import numpy as np


class VideoReaderBase(abc.ABC):
    """
    Abstract class for video_readers readers.
    """

    @abc.abstractmethod
    def __init__(self, path: Path, **kwargs):
        """
        Initializes the video_readers reader.

        Args:
            path (Path): The path to the video_readers file.
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
    def get_fps(self) -> float:
        """
        Returns the frames per second of the video_readers.

        Returns:
            float: The frames per second.
        """
        pass

    @abc.abstractmethod
    def get_path(self) -> Path:
        """
        Returns the path to the video_readers.
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def is_supported(path: Path) -> bool:
        """
        Returns whether the video_readers format is supported by the reader.

        Args:
            path (Path): The path to the video_readers file.

        Returns:
            bool: Whether the video_readers format is supported by the reader.
        """
        return False


@dataclasses.dataclass
class RegisteredVideoReader:
    """
    Dataclass for registered video_readers readers.
    """

    reader: VideoReaderBase
    priority: int


__registered_video_readers = []


def register_video_reader(reader: VideoReaderBase, priority: int = 0):
    """
    Registers a video_readers reader.

    Args:
        reader (VideoReaderBase): The video_readers reader to register.
        priority (int, optional): The priority of the reader. Defaults to 0.
    """
    __registered_video_readers.append(RegisteredVideoReader(reader, priority))
    __registered_video_readers.sort(key=lambda x: x.priority, reverse=True)


def get_video_reader(path: Path) -> VideoReaderBase:
    for reader in __registered_video_readers:
        if reader.reader.is_supported(path):
            return reader.reader(path)
    raise ValueError(f"No video_readers reader found for {path}.")
