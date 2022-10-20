import csv
from dataclasses import dataclass, field
import functools
import hashlib
import json
import logging
import math
import os
import pickle
import string
from typing import Tuple, Union

import cv2
import numpy as np

from src.dataclasses.settings import Settings
from src.media.media_types import MediaType, media_type_of
from src.utility.decorators import Singleton


@Singleton
@dataclass()
class Paths:
    _root: str = field(init=False, default=None)
    _local_storage: str = field(init=False, default="__local__storage__")
    _annotations: str = field(init=False, default="annotations")
    _datasets: str = field(init=False, default="dataset_schemes")
    _networks: str = field(init=False, default="networks")
    _resources: str = field(init=False, default="resources")
    _config: str = field(init=False, default="config.json")

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, path):
        if self._root is None and os.path.isdir(path):
            self._root = path

    @property
    def local_storage(self):
        return os.path.join(self.root, self._local_storage)

    @property
    def annotations(self):
        return os.path.join(self.local_storage, self._annotations)

    @property
    def datasets(self):
        return os.path.join(self.local_storage, self._datasets)

    @property
    def networks(self):
        return os.path.join(self.local_storage, self._networks)

    @property
    def resources(self):
        return os.path.join(self.local_storage, self._resources)

    @property
    def config(self):
        return os.path.join(self.local_storage, self._config)


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
def __footprint_of_file(path: os.PathLike, fast_hash: bool = False) -> str:
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
        path (os.PathLike): Path to .json

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


def read_csv(path: os.PathLike, data_type: np.dtype = np.float64) -> np.ndarray:
    """Read csv-file to numpy array.

    Args:
        path (os.PathLike): Input-file.
        data_type (np.dtype, optional): dtype for the created numpy array.
        Defaults to np.float64.

    Raises:
        FileNotFoundError: Raised if no file could be read.

    Returns:
        np.ndarray: Array containing the raw data.
    """
    if is_non_zero_file(path):
        has_header, delimiter = __sniff_csv__(path)
        print(has_header, delimiter)
        data = np.genfromtxt(path, delimiter=delimiter, skip_header=has_header)
        return data.astype(data_type)
    else:
        raise FileNotFoundError(f"{path} does not hold a non-empty file.")


def __sniff_csv__(path: os.PathLike) -> Tuple[bool, str]:
    """Try to read some useful information about the given csv needed for loading
    the file.

    Args:
        path (os.PathLike): Path to csv.

    Returns:
        Tuple[bool, str]: (has_header, delimiter).
    """
    # grab first few rows from the csv-file
    n_rows = 5
    with open(path, "r") as csvfile:
        lines = [csvfile.readline() for _ in range(n_rows)]

    csv_test_bytes = "".join(lines)

    # check header
    try:
        has_header = csv.Sniffer().has_header(
            csv_test_bytes
        )  # Check to see if there's a header in the file.

    except Exception:
        # heuristic approach -> check first line for non-algebraic characters
        header_line = lines[0]
        header_chars = set(header_line)
        alg_chars = set(string.digits + "," + " " + "." + "_" + "e" + "-" + "+" + "\n")
        only_alg_chars = header_chars <= alg_chars

        # if first row is already data then there is no header
        has_header = not only_alg_chars

        # check delimiter
    try:
        dialect = csv.Sniffer().sniff(csv_test_bytes)
        delimiter = dialect.delimiter
    except Exception:
        # default to ,
        delimiter = ","

    return has_header, delimiter


def write_csv(path, data: np.ndarray) -> None:
    """Write numpy-array to file.

    Args:
        path (_type_): Output path.
        data (np.ndarray): Array containing the data.
    """
    if np.issubdtype(data.dtype, np.integer):
        np.savetxt(path, data, fmt="%d", delimiter=",")
    else:
        np.savetxt(path, data, delimiter=",")


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
    """Create directory specififed by the path if it is not already
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


def meta_data(path: os.PathLike) -> Tuple[float, int, float]:
    """Compute some useful information for the given media.

    Args:
        path (os.PathLike): Path to media that should be analysed.

    Raises:
        FileNotFoundError: Raised if the given path does
        not lead to a non-zero file.

    Returns:
        Tuple[float, int, float]: Length of the media in seconds,
        Total number of frames,
        Framerate aka. sampling-rate.
    """
    if is_non_zero_file(path):
        footprint = footprint_of_file(path)
        return __meta_data__((path, footprint))
    else:
        raise FileNotFoundError


@functools.lru_cache(256)
def __meta_data__(path_and_footprint: Tuple[os.PathLike, str]):
    path, _ = path_and_footprint
    if media_type_of(path) == MediaType.LARA_MOCAP:
        meta = __meta_data_of_mocap__(path)
    elif media_type_of(path) == MediaType.VIDEO:
        meta = __meta_data_of_video__(path)
    else:
        raise ValueError(f"Could not determine media-type for {path}")
    return meta


def __meta_data_of_mocap__(path: os.PathLike) -> Tuple[int, int, float]:
    mocap = read_csv(path)
    frame_count = mocap.shape[0]
    fps = Settings.instance().refresh_rate
    return 1000 * int(frame_count / fps), frame_count, fps


def __meta_data_of_video__(path: os.PathLike) -> Tuple[int, int, float]:
    video = cv2.VideoCapture(path)
    frame_count: int = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_rate: float = video.get(cv2.CAP_PROP_FPS)
    duration: float = frame_count / frame_rate
    lower, upper = math.floor(duration), math.ceil(duration)

    d_lower = abs(lower * frame_rate - frame_count)
    d_upper = abs(upper * frame_rate - frame_count)

    # picking the better choice
    if d_lower < d_upper:
        duration: int = 1000 * lower
    else:
        duration: int = 1000 * upper

    return duration, frame_count, frame_rate


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
    log_config_dict["handlers"]["screen_handler"]["level"] = (
        "DEBUG" if Settings.instance().debugging_mode else "WARNING"
    )
    logging.config.dictConfig(log_config_dict)


# TODO
def clean_folders():
    """Check folders for unnessesary files and remove those."""
    # paths: Paths = Paths.instance()
    pass


def init_folder_structure():
    """Create all folders needed for the tool to work properly."""
    clean_folders()

    paths = Paths.instance()

    create_dir(paths.local_storage)
    create_dir(paths.annotations)
    create_dir(paths.datasets)
    create_dir(paths.networks)
    create_dir(paths.resources)
