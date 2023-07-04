import logging
from pathlib import Path

import numpy as np

from annotation_tool.utility.filehandler import checksum

from .base import MocapReaderBase, register_mocap_reader
from .cache import get_cache


def load_lara_mocap(path: Path, normalize: bool) -> np.ndarray:
    """
    Loads the LARa-mocap data from a file.

    Args:
        path (Path): The path to the LARa-mocap file.
        normalize (bool): Whether to normalize the data to the center of the coordinate system.

    Returns:
        np.ndarray: The mocap data.

    Raises:
        AssertionError: If the data type is not supported.
    """
    _hash = checksum(path)
    _key = (_hash, normalize)

    if get_cache is None:
        return __load_lara_mocap__(path, normalize)
    else:
        _cache = get_cache()

        if _key in _cache:
            return _cache[_key]
        else:
            mocap = __load_lara_mocap__(path, normalize)
            _cache[_key] = mocap
            return mocap


def __load_lara_mocap__(path: Path, normalize: bool) -> np.ndarray:
    def is_data_row(line2check: str) -> bool:
        """
        Checks if a line is a data row.
        Specific checking for the LARa dataset.

        Args:
            line2check (str): Line to check.

        Returns:
            bool: True if the line is a data row.
        """
        try:
            tst_array = np.fromstring(line2check, dtype=np.float64, sep=",")
            return tst_array.shape[0] in [132, 133, 134]
        except ValueError:
            return False

    try:
        # Check number of header lines:
        with open(path, "r") as f:
            header_lines = 0
            for line in f:
                if is_data_row(line):
                    break
                else:
                    header_lines += 1
                if header_lines > 5:
                    raise TypeError("Too many header lines in mocap file.")

        if header_lines in [1, 5]:
            array = np.loadtxt(
                path, delimiter=",", skiprows=header_lines, dtype=np.float64
            )

            if array.shape[1] == 134:
                array = array[:, 2:]

            if array.shape[1] == 133:
                array = array[:, 1:]

            if normalize:
                array = __normalize_lara_mocap__(array)

            return array
        else:
            raise TypeError("The number of header lines is not supported.")
    except Exception:
        raise TypeError("Loading mocap failed.")


def __normalize_lara_mocap__(array: np.array) -> np.array:
    """normalizes the mocap data array

    The data gets normalized by subtraction of the lower backs data from every body-segment.
    That way the lower back is in the origin.

    Arguments:
    ---------
    array : numpy.array
        2D array with normalized motioncapture data.
        1st dimension is the time
        2nd dimension is the location and rotation data of each body-segment
        shape should be (t,132) with t as number of timesteps in the data
    ---------

    Returns:
    ---------
    array : numpy.array
        2D array with normalized motioncapture data.
        1st dimension is the time
        2nd dimension is the location and rotation data of each body-segment
        shape should be (t,132) with t as number of timesteps in the data
    ---------
    """

    normalizing_vector = array[:, 66:72]  # 66:72 are the columns for lower back
    for _ in range(21):
        normalizing_vector = np.hstack((normalizing_vector, array[:, 66:72]))
    array = np.subtract(array, normalizing_vector)
    return array


class LARaMocapReader(MocapReaderBase):
    """Class for reading mocap data."""

    def __init__(self, path, **kwargs) -> None:
        """
        Initializes a new MocapReader object.

        Args:
            path (Path): The path to the mocap file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        self.path = path
        _normalize = kwargs.get("normalize", True)
        self.mocap = load_lara_mocap(self.path, _normalize)

    def get_frame(self, frame_idx: int) -> np.ndarray:
        """
        Returns the skeleton at the given frame index.

        Args:
            frame_idx (int): Frame index.

        Returns:
            np.ndarray: Skeleton at the given frame index.

        Raises:
            IndexError: If the index is out of range.
        """
        if frame_idx < 0 or frame_idx >= self.get_frame_count():
            raise IndexError("Index out of range.")

        return self.mocap[frame_idx]

    def get_frame_count(self) -> int:
        return self.mocap.shape[0]

    def get_fps(self) -> float:
        return 200.0

    def get_path(self) -> Path:
        return self.path

    @staticmethod
    def is_supported(path: Path) -> bool:
        # TODO: improve this
        try:
            load_lara_mocap(Path(path), True)
            return True
        except:  # noqa E722
            return False


register_mocap_reader(LARaMocapReader, 0)
logging.info("Registered LARa mocap reader.")
