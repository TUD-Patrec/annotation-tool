import enum
import functools
import os.path

import filetype

from src.utility import filehandler

from .media_base import MediaReader
from .mocap_reader import MocapReader, load_mocap
from .video_reader import VideoReader, get_cv


class MediaType(enum.Enum):
    UNKNOWN = 0
    VIDEO = 1
    MOCAP = 2


def media_type_of(path: os.PathLike) -> MediaType:
    footprint = filehandler.footprint_of_file(path)
    return __media_type_of__(path, footprint)


@functools.lru_cache(maxsize=128)
def __media_type_of__(path: os.PathLike, _) -> MediaType:
    if not os.path.isfile(path):
        return MediaType.UNKNOWN
    for media_type, selector in __selector_map__.items():
        if selector(path):
            return media_type
    else:
        return MediaType.UNKNOWN


def __is_video__(path: os.PathLike) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        first_check = filetype.is_video(path)
    except TypeError:
        return False

    if first_check:
        try:
            get_cv(path)  # check if cv can read the file
            return True  # cv can read the file
        except Exception:
            return False
    else:
        return False


def __is_mocap__(path: os.PathLike) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        load_mocap(path)
        return True
    except TypeError:
        return False


__selector_map__ = {MediaType.VIDEO: __is_video__, MediaType.MOCAP: __is_mocap__}


def get_reader(path: os.PathLike) -> MediaReader:
    """Returns a reader for the given path.

    Args:
        path: The path to the media file.

    Returns:
        A reader for the given path.

    Raises:
        ValueError: If the media type of the given path is not supported.
    """

    media_type = media_type_of(path)
    if media_type == MediaType.VIDEO:
        return VideoReader(path)
    elif media_type == MediaType.MOCAP:
        return MocapReader(path)
    else:
        raise ValueError("Unknown media type.")
