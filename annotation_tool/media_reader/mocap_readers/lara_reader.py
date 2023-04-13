import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

try:
    from .cache import get_cache
except ImportError:
    from cache import get_cache
except Exception:
    get_cache = None

try:
    from .base import MocapReaderBase, register_mocap_reader
except ImportError:
    from base import MocapReaderBase, register_mocap_reader


def load_lara_mocap(path: Path, data_type: np.dtype = float) -> np.ndarray:
    """
    Loads the LARa-mocap data from a file.

    Args:
        path (os.PathLike): The path to the LARa-mocap file.
        data_type (np.dtype): The data type of the returned data.

    Returns:
        np.ndarray: The mocap data.

    Raises:
        AssertionError: If the data type is not supported.
    """
    assert data_type in [
        np.float16,
        np.float32,
        np.float64,
        float,
    ], f"Invalid dtype {data_type} for mocap data."
    assert isinstance(path, Path), "Path must be a pathlib.Path object."

    if get_cache is None:
        logging.warning("Cache not available. Loading mocap from file.")
        return __load_lara_mocap__(path).astype(data_type)
    else:
        mocap_cache = get_cache()

        if path in mocap_cache:
            logging.debug(f"Loaded mocap from cache: {path}")
            return mocap_cache[path].astype(data_type)
        else:
            logging.debug(f"Loaded mocap from file: {path}")
            mocap = __load_lara_mocap__(path).astype(data_type)
            mocap_cache[path] = mocap
            return mocap


def __load_lara_mocap__(path: os.PathLike) -> np.ndarray:
    """
    Loads the LARa-mocap data from a file.
    Right now the LARa-file is expected to contain either 1 or 5 header lines.
    There should be 132 columns of data + 2 columns for the frame number and the subject.


    Args:
        path (os.PathLike): Path to motion-capture data.

    Raises:
        TypeError: If the path could not be parsed as a Motion-capture file.
    """

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
            return tst_array.shape[0] in [132, 134]
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
            array = np.loadtxt(path, delimiter=",", skiprows=header_lines)

            if array.shape[1] == 134:
                array = array[:, 2:]

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
            path (os.PathLike): The path to the mocap file.
            fps (float): The framerate of the mocap data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        self.path = path
        self._dtype = kwargs.get("dtype", float)
        self.mocap = load_lara_mocap(Path(self.path), self._dtype)

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

    def get_fps(self) -> Optional[float]:
        return None

    def get_duration(self) -> float:
        return None

    def get_path(self) -> os.PathLike:
        return self.path

    @staticmethod
    def is_supported(path: os.PathLike) -> bool:
        # TODO: improve this
        try:
            load_lara_mocap(Path(path))
            return True
        except:  # noqa E722
            return False


register_mocap_reader(LARaMocapReader, 0)
logging.info("Registered LARa mocap reader.")
