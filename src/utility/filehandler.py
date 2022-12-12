import csv
import fnmatch
import functools
import hashlib
import json
import logging
import logging.config
import os
import pickle
import string
from typing import List, Tuple, Union

import numpy as np


def find_all(name: str, path: os.PathLike = None) -> list:
    """Find all files with the given name in the given path. If no path is
    given, the user's home directory is used.

        Args:
            name (str): Name of the file.
            path (os.PathLike, optional): Path to search in. Defaults to None.

        Returns:
            list: List of all files with the given name.

        Raises:
            ValueError: If no path is given.
    """
    if name is None or name == "":
        raise ValueError("name must not be empty")
    if path is None:
        path = os.path.join(os.path.expanduser("~"))
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def find_all_p(pattern: str, path: os.PathLike) -> list:
    """Find all files matching the given pattern in the given path.
    If no path is given, the user's home directory is used.

    Args:
        pattern (str): Pattern to match.
        path (os.PathLike): Path to search in.

    Returns:
        list: List of all files matching the given pattern.
    """
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def find_first(name: str, path: os.PathLike = None) -> Union[str, None]:
    """Find first file with the given name in the given path. If no path is
    given, the user's home directory is used.

    Args:
        name (str): Name of the file.
        path (os.PathLike, optional): Path to search in. Defaults to None.

    Returns:
        Union[str, None]: Path to the first file found or None.
    """
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None


def is_non_zero_file(path: os.PathLike) -> bool:
    """Check if file exists and is non-empty.

    Args:
        path (os.PathLike): file-path.

    Returns:
        bool: True if file is non-zero.
    """
    return os.path.isfile(path) and os.path.getsize(path) > 0


def footprint_of_file(path: os.PathLike, fast_hash: bool = False) -> Union[str, None]:
    """Return unique ID for the given path

    Args:
        path (os.PathLike): Location of the file.
        fast_hash (bool, optional): Fast-hash uses a more simple methode
        to approximate the ID of the file. Defaults to False.

    Returns:
        Union[str, None]: Hash-value computed for the specified file or None.
    """
    if is_non_zero_file(path):
        return __footprint_of_file(path, fast_hash)
    else:
        return None


@functools.lru_cache(maxsize=256)
def __footprint_of_file(path: os.PathLike, fast_hash: bool = True) -> str:
    if fast_hash:
        return __fast_footprint__(path)
    else:
        return __generate_file_md5__(path)


def __fast_footprint__(path: os.PathLike) -> str:
    with open(path, "rb") as f:
        x = f.read(2**20)
    x = int.from_bytes(x, byteorder="big", signed=True)
    x %= 2**32
    x ^= os.path.getsize(path)
    return str(x)


def __generate_file_md5__(path: os.PathLike, block_size: int = 2**20) -> str:
    m = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            buf = f.read(block_size)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def read_json(path: os.PathLike) -> Union[dict, None]:
    """Try reading .json-file from the specified path.

    Args:
        path (os.PathLike): Path to the .json-file.

    Returns:
        Union[dict, None]: Dictionary containing the values
        read from the .json.
    """
    if is_non_zero_file(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except ValueError:
            return None
    else:
        return None


def write_json(path: os.PathLike, data: dict) -> None:
    """Write values from dict to a json-file.

    Args:
        path (os.PathLike): Path to the output-file.
        data (dict): Data to be written.
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def __sniff_csv__(path: os.PathLike) -> Tuple[int, str]:
    """
    Try to read some useful information about the given csv needed for loading
    the file.

    Args:
        path (os.PathLike): Path to csv.

    Returns:
        Tuple[int, str]: (#Header_Rows, delimiter).
    """
    # grab first few rows from the csv-file
    n_rows = 10
    with open(path, "r") as csvfile:
        lines = [csvfile.readline() for _ in range(n_rows)]

    n_headers = 0

    while __has_header__("".join(lines[n_headers:])):
        n_headers += 1

    csv_test_bytes = "".join(lines)

    # check delimiter
    try:
        dialect = csv.Sniffer().sniff(csv_test_bytes, delimiters=",;")
        delimiter = dialect.delimiter
    except Exception:
        # defaults to ,
        delimiter = ","

    return n_headers, delimiter


def __has_header__(csv_test_bytes: str) -> bool:
    def __heuristic_header_check__(csv_test_bytes: str) -> bool:
        # heuristic approach -> check first line for non-algebraic characters
        header_line = csv_test_bytes.split("\n")[0]
        header_chars = set(header_line)
        alg_chars = set(string.digits + "," + " " + "." + "_" + "e" + "-" + "+" + "\n")
        only_alg_chars = header_chars <= alg_chars

        # if first row is already data then there is no header
        has_header = not only_alg_chars
        return has_header

    # check header
    try:
        has_header = csv.Sniffer().has_header(
            csv_test_bytes
        )  # Check to see if there's a header in the file.
        return has_header or __heuristic_header_check__(csv_test_bytes)
    except Exception:
        # only use __heuristic_header__check result
        return __heuristic_header_check__(csv_test_bytes)


def read_csv(
    path: os.PathLike, data_type: np.dtype = np.float64, NaN_behavior: str = "remove"
) -> np.ndarray:
    """Read csv-file to numpy array.

    Args:
        path (os.PathLike): Input-file.
        data_type (np.dtype, optional): dtype for the created numpy array.
        Defaults to np.float64.
        NaN_behavior (str, optional): behavior of how NaN-Rows should be treated.
        Possible Values are "remove" -> removes row,
        "keep" (Same as None) -> keeps NaN Values,
        "zero" -> replaces each NaN by 0

    Raises:
        FileNotFoundError: Raised if no file could be read.

    Returns:
        np.ndarray: Array containing the raw data.
    """
    n_headers, delimiter = __sniff_csv__(path)
    data = np.genfromtxt(path, delimiter=delimiter, skip_header=n_headers)

    if NaN_behavior is None or NaN_behavior == "keep":
        pass
    elif NaN_behavior == "remove":
        data = data[~np.isnan(data).any(axis=1)]
    elif NaN_behavior == "zero":
        data = np.nan_to_num(data)
    else:
        raise ValueError(f"NaN_behavior {NaN_behavior} is not a valid input!")

    data = data.astype(data_type)
    return data


def write_csv(path: os.PathLike, data: np.ndarray, header: List[str] = None) -> None:
    """Write numpy-array to file.

    Args:
        path (os.PathLike): Output path.
        data (np.ndarray): Array containing the data.
        header (List[str], optional): Header for the csv-file.
    """
    if header is not None:
        header = ",".join(header)
    else:
        header = ""
    if np.issubdtype(data.dtype, np.integer):
        np.savetxt(path, data, fmt="%d", delimiter=",", header=header)
    else:
        np.savetxt(path, data, delimiter=",", header=header)


def write_pickle(path: os.PathLike, data: object) -> None:
    """Freeze object and store as file.

    Args:
        path (os.PathLike): Output path.
        data (object): Object to be stored.
    """
    if data:
        with open(path, "wb") as f:
            pickle.dump(data, f)


def read_pickle(path: os.PathLike) -> object:
    """Read stored object from file.

    Args:
        path (os.PathLike): Path to object.

    Returns:
        object: Object loaded from disk.
    """
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def create_dir(path: os.PathLike) -> os.PathLike:
    """Create directory specified by the path if it is not already
    existing.

    Args:
        path (os.PathLike): Path to directory.

    Returns:
        os.PathLike: Path to newly created directory.
    """
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def remove_file(path: os.PathLike) -> None:
    """Remove file from file-system.

    Args:
        path (os.PathLike): File that should be removed.
    """
    if os.path.isfile(path):
        os.remove(path)


def path_to_filename(path: os.PathLike) -> str:
    """Grab the filename from a given file-path.

    Args:
        path (os.PathLike): Absolute path to some object on
        the file-system.

    Returns:
        os.PathLike: Filename.
    """
    if os.path.isfile(path):
        filename = os.path.split(path)[-1]
        return filename.split(".")[0]


def path_to_dirname(path: os.PathLike) -> os.PathLike:
    """Grab path to parent-directory of some path.

    Args:
        path (os.PathLike): Absolute path to some object on
        the file-system.

    Returns:
        os.PathLike: Path to parent-directory.
    """
    if os.path.isdir(path):
        dirname = os.path.split(path)[-1]
        return dirname


def logging_config() -> dict:
    """Create basic configuration for logging.

    Returns:
        dict: Configuration-dict.
    """
    return {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "screen": {
                "format": "[%(asctime)s] [%(levelname)s] [%(filename)s():%(lineno)s] - %(message)s",  # noqa: E501
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "full": {
                "format": "[%(asctime)s] [%(levelname)s] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "screen_handler": {
                "level": "WARNING",
                "formatter": "screen",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {"handlers": ["screen_handler"], "level": "DEBUG", "propagate": False}
        },
    }


def init_logger():
    from src.settings import settings

    """Initialize logger."""
    log_config_dict = logging_config()
    log_config_dict["handlers"]["screen_handler"]["level"] = (
        "DEBUG" if settings.debugging_mode else "WARNING"
    )
    logging.config.dictConfig(log_config_dict)
