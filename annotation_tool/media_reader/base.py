import abc
import functools
import logging
import os
from pathlib import Path
import time
from typing import Optional, Tuple

import numpy as np


class MediaReader(abc.ABC):
    """
    Baseclass for media readers (e.g. video, mocap, etc.)
    """

    @abc.abstractmethod
    def __init__(self, path: Path, **kwargs) -> None:
        """
        Initializes a new __MediaReader object.

        Args:
            path: The path to the media file.
            kwargs: {fps: The framerate of the media data., n_frames: The number of frames in the media data.}

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not path.is_file():
            raise FileNotFoundError(f"File {path} does not exist.")

    @property
    def duration(self) -> int:
        """
        Returns the duration of the media in milliseconds.
        """
        return int(len(self) / self.fps) * 1000

    @property
    def fps(self) -> float:
        return self.__get_fps__()

    @property
    def path(self) -> Path:
        return self.__get_path__()

    @property
    def media_type(self) -> str:
        return media_type_of(self.path)

    def __len__(self):
        return self.__get_frame_count__()

    def __getitem__(self, idx):
        """
        Returns the frame at the given index.
        If the index is a slice, returns a list of frames.
        The shape of the frame depends on the media type, e.g. for video it is (h,w,c) with c being the 3-RGB channels.

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

    def __iter__(self):
        return self[:]

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

    @abc.abstractmethod
    def __get_frame_count__(self) -> int:
        """
        Returns the number of frames in the media file.

        Returns:
            The number of frames in the media file.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __get_fps__(self) -> Optional[float]:
        """
        Detects the framerate of the media file.

        Returns:
            The framerate of the media file if it can be detected, None otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __get_path__(self) -> Path:
        """
        Returns the path to the media file.

        Returns:
            The path to the media file.
        """
        raise NotImplementedError

    def numpy(self, lo: int, hi: int, step: int = 1):
        """
        Returns a numpy array of the frames between lo and hi.

        Args:
            lo: The lower bound of the frame indices.
            hi: The upper bound of the frame indices.
            step: The step size between frames.
        Returns:
            A numpy array of the frames between lo and hi with step size step.
        """
        return np.array([self[i] for i in range(lo, hi, step)])


class __MediaSelector:
    def __init__(self):
        self._selector_functions = {}

    def register(self, media_type: str, selector_function: callable) -> None:
        """
        Registers a new media type.

        Args:
            media_type: The name of the media type.
            selector_function: A function that takes a path and returns True if the path is of the given media type.

        Raises:
            TypeError: If the media_type is not a string or the selector_function is not a callable.
        """
        media_type = media_type.lower()
        if not isinstance(media_type, str):
            raise TypeError(f"Invalid argument type {type(media_type) = }")
        if not callable(selector_function):
            raise TypeError(f"Invalid argument type {type(selector_function) = }")
        self._selector_functions[media_type] = selector_function

    def select(self, path: Path) -> Optional[str]:
        """
        Selects the media type of the given path.

        Args:
            path: The path to the media file.
        Returns:
            The media type of the given path.
        Raises:
            ValueError: If the media type could not be determined.
        """
        for media_type, selector_function in self._selector_functions.items():
            if selector_function(path):
                return media_type
        return None


class __MediaFactory:
    def __init__(self):
        self._builders = {}

    def register(self, media_type: str, factory: callable) -> None:
        """
        Registers a new media factory.

        Args:
            media_type: The name of the media type.
            factory: A function that takes a path and returns a new __MediaReader object.

        Raises:
            TypeError: If the media_type is not a string or the factory is not a callable.
        """
        media_type = media_type.lower()
        if not isinstance(media_type, str):
            raise TypeError(f"Invalid argument type {type(media_type) = }")
        if not callable(factory):
            raise TypeError(f"Invalid argument type {type(factory) = }")
        self._builders[media_type] = factory

    def create(self, media_type: str, **kwargs) -> MediaReader:
        """
        Creates a new MediaReader object.

        Args:
            media_type: The name of the media type.
            **kwargs: The arguments to pass to the factory function.

        Returns:
            A new MediaReader object.
        """
        media_type = media_type.lower()
        factory = self._builders.get(media_type)
        if factory is None:
            raise ValueError(f"Unsupported media type: {media_type}")
        return factory(**kwargs)


# Global variables, should be singleton instances
__media_selector__ = __MediaSelector()
__media_factory__ = __MediaFactory()


def register_media_reader(
    media_type: str, selector_function: callable, factory: callable
) -> None:
    """
    Registers a new media reader.

    Args:
        media_type: The name of the media type.
        selector_function: A function that takes a path and returns True if the path is of the given media type.
        factory: A function that takes a path and returns a new MediaReader object.

    Raises:
        TypeError: If the media_type is not a string or the selector_function or factory is not a callable.
    """
    __media_selector__.register(media_type, selector_function)
    __media_factory__.register(media_type, factory)


def media_reader(path: Path, **kwargs) -> MediaReader:
    """
    Returns a MediaReader for the given path.

    Args:
        path: The path to the media file.

    Returns:
        A MediaReader for the given path.

    Raises:
        ValueError: If the media type could not be determined.
    """
    if not isinstance(path, Path):
        raise TypeError(f"Invalid argument type {type(path) = }")

    start = time.perf_counter()
    media_type = __media_selector__.select(path)
    mr = __media_factory__.create(media_type, path=path, **kwargs)
    end = time.perf_counter()

    logging.debug(
        f"Created {media_type} reader for {path} in {end - start:.4f} seconds."
    )

    return mr


def media_type_of(path: Path) -> str:
    """
    Returns the media type of the given path.

    Args:
        path: The path to the media file.

    Returns:
        The media type of the given path.
    """
    return __media_selector__.select(path)


@functools.lru_cache(maxsize=None)
def _meta_data(file: Path, identifier: Tuple) -> dict:
    """
    The identifier-arg is only used for caching.
    """
    mr = media_reader(file)
    return {
        "fps": mr.fps,
        "n_frames": len(mr),
        "duration": mr.duration,
        "media_type": mr.media_type,
    }


def meta_data(file: Path) -> dict:
    """
    Returns the metadata of the media file. The metadata is a dictionary with the following keys:
        - fps: (float) The framerate of the media.
        - n_frames: (int) The number of frames in the media.
        - duration: (int) The duration of the media in milliseconds.
        - media_type: (str) The type of the media (e.g. video, mocap, etc.).

    The values are cached, so this function can be called multiple times without performance loss.
    This is the preferred way to get information about the media file.
    Use this if you don't need the actual media data.

    Args:
        file: The path to the media file.

    Returns:
        dict: The metadata. If the file does not exist, an empty dictionary is returned.
    """
    try:
        last_change = int(os.path.getmtime(file))
        size = os.path.getsize(file)
        identifier = (last_change, size)
        return _meta_data(file, identifier)
    except FileNotFoundError:
        return {}
