import enum


class MediaType(enum.Enum):
    UNKNOWN = 0
    VIDEO = 1
    MOCAP = 2
    IMU = 3


__str_map__ = {x.name: x for x in MediaType}


def to_str(media_type: MediaType) -> str:
    """
    Returns the string representation of a media type.

    Args:
        media_type: The media type.
    Returns:
        The string representation of the media type.
    """
    return media_type.name


def from_str(media_type: str) -> MediaType:
    """
    Returns the media type from a string.

    Args:
        media_type: The string representation of the media type.

    Returns:
        The media type.
    """
    media_type = media_type.upper()
    res = __str_map__.get(media_type, None)
    if res is None:
        raise ValueError(f"Unknown media type: {media_type}")
    return res
