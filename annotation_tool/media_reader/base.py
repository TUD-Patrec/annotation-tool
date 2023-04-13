import abc
import logging
import os
from typing import Optional, Union

import numpy as np

__FALLBACK_FPS__ = 30  # fallback framerate if no framerate can be determined


def set_fallback_fps(fps: float) -> None:
    """
    Sets the fallback framerate.

    Args:
        fps: The fallback framerate.
    """
    if isinstance(fps, (int, float)):
        logging.debug(f"Setting fallback framerate to {fps}.")
        global __FALLBACK_FPS__
        __FALLBACK_FPS__ = fps
    else:
        raise TypeError("Framerate must be a number.")


def get_fallback_fps() -> Union[int, float]:
    """
    Returns the fallback framerate.

    Returns:
        The fallback framerate.
    """
    return __FALLBACK_FPS__


class MediaReader(abc.ABC):
    """
    Baseclass for media readers (e.g. video, mocap, etc.)
    """

    @abc.abstractmethod
    def __init__(self, path: os.PathLike, **kwargs) -> None:
        """
        Initializes a new __MediaReader object.

        Args:
            path: The path to the media file.
            kwargs: {fps: The framerate of the media data., n_frames: The number of frames in the media data.}

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} does not exist.")

    @property
    def duration(self) -> int:
        """
        Returns the duration of the media in milliseconds.
        """
        try:
            _duration = self.__get_duration__()
        except NotImplementedError:
            _duration = None
        if _duration:
            return int(self.__get_duration__()) * 1000
        else:
            return int(len(self) / self.fps) * 1000

    @property
    def fps(self) -> float:
        _fps = self.__get_fps__()
        if _fps:
            return _fps
        else:
            return get_fallback_fps()

    @fps.setter
    def fps(self, fps: Union[int, float]) -> None:
        self.__set_fps__(fps)

    @property
    def path(self) -> os.PathLike:
        return self.__get_path__()

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
    def __get_duration__(self) -> Optional[float]:
        """
        Returns the duration of the media in seconds.
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
    def __get_path__(self) -> os.PathLike:
        """
        Returns the path to the media file.

        Returns:
            The path to the media file.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __set_fps__(self, fps: Union[int, float]) -> None:
        """
        Sets the framerate of the media file.

        Args:
            fps: The framerate to set.
        """
        raise NotImplementedError


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

    def select(self, path: os.PathLike) -> Optional[str]:
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


def media_reader(path: os.PathLike, **kwargs) -> MediaReader:
    """
    Returns a MediaReader for the given path.

    Args:
        path: The path to the media file.

    Returns:
        A MediaReader for the given path.

    Raises:
        ValueError: If the media type could not be determined.
    """

    media_type = __media_selector__.select(path)
    mr = __media_factory__.create(media_type, path=path, **kwargs)

    return mr


def media_type_of(path: os.PathLike) -> str:
    """
    Returns the media type of the given path.

    Args:
        path: The path to the media file.

    Returns:
        The media type of the given path.
    """
    return __media_selector__.select(path)
