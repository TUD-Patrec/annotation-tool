import enum
import os.path

import cv2
import filetype

from src.utility import filehandler


class MediaType(enum.Enum):
    UNKNOWN = 0
    VIDEO = 1
    LARA_MOCAP = 2


def is_video(path) -> bool:
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
        except Exception as e:
            return False
    else:
        return False


def is_LARA_mocap(path) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        data = filehandler.csv_to_numpy(path)
        return data.shape[0] > 0 and data.shape[1] == 134
    except UserWarning as u:
        return False
    except Exception as e:
        return False


selector_map = {MediaType.VIDEO: is_video, MediaType.LARA_MOCAP: is_LARA_mocap}


__cached_media_types__ = {}


def media_type_of(path, use_cache=True) -> MediaType:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{path} was not found on the system.")

    if use_cache:
        media_type = __cached_media_types__.get(path)
        if media_type:
            return media_type
    for x in MediaType:
        if x == MediaType.UNKNOWN:
            continue
        else:
            test_media_type = selector_map[x]
            if test_media_type(path):
                __cached_media_types__[path] = x
                return x

    unknown_media_type = MediaType.UNKNOWN
    __cached_media_types__[path] = unknown_media_type
    return unknown_media_type
