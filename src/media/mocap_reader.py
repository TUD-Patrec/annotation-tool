from functools import lru_cache
import os

import numpy as np

from .media_base import MediaReader


def get_mocap(*args):
    return load_mocap(*args)


@lru_cache(maxsize=10)
def load_mocap(path: os.PathLike, data_type: np.dtype = np.float32) -> np.ndarray:
    """
    Load Motion-capture data from file to numpy array.
    The mocap data is cached, so that the same mocap data is not loaded twice.

    Args:
        path (os.PathLike): Path to motion-capture data.
        data_type (np.dtype, optional): Data type of the returned array. Defaults to np.float32.
    Raises:
        TypeError: If the path could not be parsed as a Motion-capture file.

    Returns:
        np.ndarray: Array containing the loaded motion-capture data.
    """
    try:
        array = __load_lara_mocap__(path)
        print("array.shape", array.shape)
        print("memory size = ", array.nbytes / 1024 / 1024, "MB")
        return array.astype(data_type)
    except TypeError as e:
        raise TypeError("Loading mocap failed.") from e


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


class MocapReader(MediaReader):
    """Class for reading mocap data."""

    def __init__(self, path: os.PathLike) -> None:
        """
        Initializes a new MocapReader object.

        Args:
            path (os.PathLike): The path to the mocap file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

        super().__init__(path)
        self._n_frames = self.media.shape[0]

    def __get_frame__(self, idx: int) -> np.ndarray:
        """
        Returns the skeleton at the given frame index.

        Args:
            idx (int): Frame index.

        Returns:
            np.ndarray: Skeleton at the given frame index.

        Raises:
            IndexError: If the index is out of range.
        """
        if idx < 0 or idx >= len(self):
            raise IndexError("Index out of range.")

        return self.media[idx]
