import csv
import hashlib
import json
import logging
import logging.config
import os
from pathlib import Path
import string
from typing import List, Tuple, Union

import numpy as np


def is_non_zero_file(path: Path) -> bool:
    """Check if file exists and is non-empty.

    Args:
        path (Path): file-path.

    Returns:
        bool: True if file is non-zero.
    """
    return path.is_file() and os.path.getsize(path) > 0


def __approx_md5__(path: Path, n_blocks=20, block_size=2**12) -> str:
    m = hashlib.md5()

    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        # np.linspace might overflow for large files, standard python int is safer
        start_positions = [
            int(file_size * i / (n_blocks - 1)) for i in range(n_blocks)
        ]  # linearly spaced start positions
        _last_pos = -1  # for early stopping

        for start_pos in start_positions:
            end_pos = start_pos + block_size
            if end_pos > file_size:
                start_pos = max(0, file_size - block_size)
                end_pos = file_size

            if start_pos == _last_pos:
                break  # avoid reading the same block twice

            f.seek(start_pos)  # seek to start position

            _block_size = (
                end_pos - start_pos
            )  # actual block size (might be smaller than block_size)
            buf = f.read(_block_size)  # read block

            m.update(buf)  # update hash

            _last_pos = start_pos

    return m.hexdigest()


def checksum(path: Path) -> str:
    """Return unique ID for the given path. The ID is computed by
    hashing some parts of the file and appending the file-size.
    The runtime of this function is independent of the file-size and only depends on the number of blocks and the block-size.

    Note: This is not a cryptographic hash-function and should not be used as such.

    Args:
        path (Path): Location of the file.
    Returns:
        str: Hash-value computed for the specified file.
    """
    if is_non_zero_file(path):
        _md5 = __approx_md5__(path)
        _size = os.path.getsize(path)
        res = f"{_md5}_{_size}B"
        return res
    else:
        raise FileNotFoundError(f"File {path} does not exist or is empty.")


def read_json(path: Path) -> dict:
    """Try reading .json-file from the specified path.

    Args:
        path (Path): Path to the .json-file.

    Returns:
        Union[dict, None]: Dictionary containing the values
        read from the .json.
    """
    if is_non_zero_file(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"File {path} does not exist or is empty.")


def write_json(path: Path, data: Union[dict, List]) -> None:
    """Write values from dict to a json-file.

    Args:
        path (Path): Path to the output-file.
        data (Union[dict, List]): Data to be written.
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def __sniff_csv__(path: Path) -> Tuple[int, str]:
    """
    Try to read some useful information about the given csv needed for loading
    the file.

    Args:
        path (Path): Path to csv.

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
    path: Path, data_type: np.dtype = np.float64, NaN_behavior: str = "remove"
) -> np.ndarray:
    """Read csv-file to numpy array.

    Args:
        path (Path): Input-file.
        data_type (np.dtype, optional): dtype for the created numpy array.
        Defaults to np.float64.
        NaN_behavior (str, optional): behavior of how NaN-Rows should be treated.
        Possible Values are "remove" -> removes row,
        "keep" (Same as None) -> keeps NaN Values,
        "zero" -> replaces each NaN by 0

    Raises:
        FileNotFoundError: Raised if no file could be read.
        ValueError: Raised if NaN_behavior is not a valid input.

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


def write_csv(path: Path, data: np.ndarray, header: List[str] = None) -> None:
    """Write numpy-array to file.

    Args:
        path (Path): Output path.
        data (np.ndarray): Array containing the data.
        header (List[str], optional): Header for the csv-file.
    """
    if header is not None:
        header = ",".join(header)
    else:
        header = ""
    if np.issubdtype(data.dtype, np.integer):
        np.savetxt(path, data, fmt="%d", delimiter=",", header=header, comments="")
    else:
        np.savetxt(path, data, delimiter=",", header=header, comments="")


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
    """Initialize logger."""
    log_config_dict = logging_config()
    log_config_dict["handlers"]["screen_handler"]["level"] = "WARNING"
    logging.config.dictConfig(log_config_dict)


def set_logging_level(level: Union[int, str]) -> None:
    """Set logging level.

    Args:
        level (Union[int, str]): Logging level. Possible values are
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
    """
    if isinstance(level, str):
        level = level.upper()
    else:
        level = logging.getLevelName(level)
    try:
        log_config_dict = logging_config()
        log_config_dict["handlers"]["screen_handler"]["level"] = level
        logging.config.dictConfig(log_config_dict)
    except ValueError:
        # default to WARNING
        set_logging_level("WARNING")
        logging.error(f"Logging level {level} is not a valid input!")
