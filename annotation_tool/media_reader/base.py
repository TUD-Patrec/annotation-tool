import abc
import logging
import os
from typing import Optional, Union

import cv2 as cv
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

    def __init__(self, path: os.PathLike, **kwargs) -> None:
        """
        Initializes a new __MediaReader object.

        Args:
            path: The path to the media file.
            kwargs: {fps: The framerate of the media data., n_frames: The number of frames in the media data.}

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        # check parameters
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        self._path: os.PathLike = path

        if "fps" in kwargs:
            fps = kwargs["fps"]
            assert (
                isinstance(fps, (int, float)) and fps > 0 or fps is None
            ), f"Framerate must be a positive number or None, not {fps}."
            self._fps = fps
        else:
            self._fps = self.__detect_fps__()

        if "n_frames" in kwargs:
            n_frames = kwargs["n_frames"]
            assert (
                isinstance(n_frames, int) and n_frames > 0
            ), f"Number of frames must be an positive integer, not {n_frames}."
            self._n_frames = n_frames
        else:
            self._n_frames = self.__detect_n_frames__()

    @property
    def path(self) -> os.PathLike:
        return self._path

    @property
    def duration(self) -> int:
        """
        Returns the duration of the media in milliseconds.
        """
        return int(self.n_frames / self.fps) * 1000

    @property
    def fps(self) -> float:
        if self._fps:
            return self._fps
        else:
            return get_fallback_fps()

    @fps.setter
    def fps(self, fps: Union[int, float]) -> None:
        if isinstance(fps, (int, float)):
            self._fps = fps
        else:
            raise TypeError("Framerate must be a number.")

    @property
    def n_frames(self) -> int:
        return self._n_frames

    @property
    def media(self):
        return __memoizer__(self)

    def raw_fps(self) -> Optional[float]:
        """
        Returns the framerate of the media data.
        If the framerate cannot be determined, returns None.

        Returns:
            The framerate of the media data.
        """
        return self._fps

    def __len__(self):
        return self.n_frames

    def __eq__(self, other) -> bool:
        if isinstance(other, MediaReader):
            return self.id == other.id
        return False

    def __del__(self):
        __memoizer__.remove(self)

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

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
    def __read_media__(self):
        """
        Reads the media file.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __detect_fps__(self) -> Optional[float]:
        """
        Detects the framerate of the media file.

        Returns:
            The framerate of the media file if it can be detected, None otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __detect_n_frames__(self) -> int:
        """
        Detects the number of frames in the media file.

        Returns:
            The number of frames in the media file.
        """
        raise NotImplementedError


class __Memoizer:
    def __init__(self):
        self._cache = {}

    def __call__(self, mr: MediaReader) -> Union[cv.VideoCapture, np.ndarray]:
        """
        Returns the memorized version of the given __MediaReader.

        Args:
            mr: The __MediaReader to memorize.

        Returns:
            The memorized version of the __MediaReader.
        """
        if not isinstance(mr, MediaReader):
            raise TypeError("Invalid argument type.")
        key = id(mr)
        if key not in self._cache:
            media = mr.__read_media__()
            self._cache[key] = media

        return self._cache[key]

    def remove(self, mr: MediaReader) -> None:
        """
        Removes the given __MediaReader from the cache.

        Args:
            mr: The __MediaReader to remove.
        """
        key = id(mr)
        if key in self._cache:
            del self._cache[key]
            logging.debug(f"Removed {mr} from cache. Cache size: {len(self._cache)}")


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
__memoizer__ = __Memoizer()
__media_selector__ = __MediaSelector()
__media_factory__ = __MediaFactory()
__kwarg_dict__ = {}


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


def media_reader(path: os.PathLike, **ignored) -> MediaReader:
    """
    Returns a MediaReader for the given path.

    Args:
        path: The path to the media file.
        **kwargs: Additional arguments to pass to the MediaReader constructor.

    Returns:
        A MediaReader for the given path.

    Raises:
        ValueError: If the media type could not be determined.
    """

    kwargs = __kwarg_dict__.get(path, {})

    media_type = __media_selector__.select(path)
    mr = __media_factory__.create(media_type, path=path, **kwargs)

    __kwarg_dict__[path] = {
        "fps": mr.raw_fps(),
        "n_frames": mr.n_frames,
    }  # fps-property hides None-values, raw_fps() does not

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
