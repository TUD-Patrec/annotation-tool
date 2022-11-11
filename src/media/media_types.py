import enum
import functools
import os.path

import cv2
import filetype

from src.media.mocap_reading import load_mocap
from src.utility import filehandler


class MediaType(enum.Enum):
    UNKNOWN = 0
    VIDEO = 1
    MOCAP = 2


def media_type_of(path: os.PathLike) -> MediaType:
    footprint = filehandler.footprint_of_file(path)
    return __media_type_of__(path, footprint)


@functools.lru_cache(maxsize=128)
def __media_type_of__(path, _) -> MediaType:
    if not os.path.isfile(path):
        return MediaType.UNKNOWN
    for media_type, selector in __selector_map__.items():
        if selector(path):
            return media_type
    else:
        return MediaType.UNKNOWN


def __is_video__(path) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        first_check = filetype.is_video(path)
    except TypeError:
        return False

    if first_check:
        try:
            video = cv2.VideoCapture(path)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count > 0:
                ret, frame = video.read()
                return ret
            else:
                return False
        except Exception:
            return False
    else:
        return False


def __is_mocap__(path) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        load_mocap(path)
        return True
    except TypeError:
        return False


__selector_map__ = {MediaType.VIDEO: __is_video__, MediaType.MOCAP: __is_mocap__}
