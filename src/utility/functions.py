import functools
import os
from typing import Tuple

from src.dataclasses.settings import Settings

from ..dataclasses.datasets import DatasetDescription
from ..dataclasses.globalstate import GlobalState
from .decorators import Singleton
from .filehandler import Paths, is_non_zero_file


def scale(N: int, M: int, x: int) -> Tuple[int, int]:
    """Scaling function that scales some point x within a range
    of N elements to another range of M elements while keeping its
    relative position inside that range.
    Scaling from some smaller range to a bigger one ends maps one point
    into a interval of possibly multiple-points.
    Args:
        N (int): Size of the initial range.
        M (int): Size of the new range.
        x (int): Point inside the initial range that will be mapped.

    Raises:
        ValueError: Raised if any of the input-values is not an integer.

    Returns:
        Tuple[int, int]: Closed interval in the new range where the
        initial point is mapped onto.
    """
    if isinstance(N, int) and isinstance(M, int) and isinstance(x, int):
        if N == M:
            return x, x
        elif N > M:
            return (x * M) // N, (x * M) // N
        elif N < M:
            lo = (x * M) // N if (x * M) % N == 0 else (x * M) // N + 1
            hi = (
                ((x + 1) * M) // N - 1 if ((x + 1) * M) % N == 0 else ((x + 1) * M) // N
            )
            return lo, hi
    else:
        raise ValueError


def scale_functions(N: int, M: int, last_to_last: bool = False):
    """Create scaling functions

    Args:
        N (int): Number of elements in the first range.
        M (int): Number of elements in the second range.
        last_to_last (bool, optional): Sometimes its useful if the last elements
            of two ranges always map to each other. Defaults to False.

    Returns:
        n2m: function: Map from n to m.
        m2n: function. Map from m to n.
    """
    offset = int(last_to_last) if N > 1 and M > 1 else 0
    n2m = functools.partial(scale, N - offset, M - offset)
    m2n = functools.partial(scale, M - offset, N - offset)

    return n2m, m2n


def ms_to_time_string(ms: int) -> str:
    """Create a human readable representation for the given milliseconds.

    Args:
        ms (int): Milliseconds.

    Returns:
        str: String representation formatted as mm:ss:mm.
    """
    mins = ms // (60 * 1000)
    ms %= 60 * 1000
    secs = ms // 1000
    ms %= 1000
    return "{:02d}:{:02d}:{:03d}".format(mins, secs, ms)


def get_datasets() -> list:
    """Read all stored datasets from disk.

    Returns:
        list: List of datasets.
    """
    datasets = []
    for file in os.listdir(Paths.instance().datasets):
        file_path = os.path.join(Paths.instance().datasets, file)
        if is_non_zero_file(file_path):
            data_description = DatasetDescription.from_disk(file_path)
            datasets.append(data_description)
    datasets.sort(key=lambda x: x.name)
    return datasets


def get_annotations() -> list:
    """Read all annotation files from disk.

    Returns:
        list: List of annotations.
    """
    annotations = []
    for file in os.listdir(Paths.instance().annotations):
        file_path = os.path.join(Paths.instance().annotations, file)
        if is_non_zero_file(file_path):
            annotation = GlobalState.from_disk(file_path)
            annotations.append(annotation)
    annotations.sort(key=lambda x: x.name)
    return annotations


@Singleton
class FrameTimeMapper:
    """Simple helper class to ease the use of the scaling functions for
    the specific case of mapping between frame-positions within some media
    and the corresponding timestamp.
    """

    def __init__(self) -> None:
        self.use_time = Settings.instance().show_millisecs
        self.n_frames = 1
        self.millisecs = 1
        self._frame_to_ms, self._ms_to_frame = scale_functions(1, 1, True)

    def update(self, n_frames: int = None, millisecs: int = None) -> None:
        """Update the state of the Mapper. Changes the two ranges and updates
        the mapping functions.

        Args:
            n_frames (int, optional): Number of frames inside the media.
            Defaults to None.
            millisecs (int, optional): Duration of the media in milliseconds.
            Defaults to None.
        """
        if n_frames:
            self.n_frames = n_frames
        if millisecs:
            self.millisecs = millisecs
        self.use_time = Settings.instance().show_millisecs

        self._frame_to_ms, self._ms_to_frame = scale_functions(
            self.n_frames, self.millisecs, True
        )

    def frame_repr(self, frame: int) -> str:
        """Get representation of current frame-position.

        Args:
            frame (int): Current frame position.

        Returns:
            str: Readable representation of the current position.
        """
        if self.use_time:
            millisecs = self._frame_to_ms(frame)[0]
            return ms_to_time_string(millisecs)
        else:
            return str(frame)

    def frame_to_ms(self, frame: int) -> int:
        """Map frame-position to time-position.

        Args:
            frame (int): Index to current frame.

        Returns:
            int: Timestamp corresponding to current frame
        """
        return self._frame_to_ms(frame)[0]

    def ms_to_frame(self, ms: int) -> int:
        """Map time-position to frame-position.

        Args:
            ms (int): Timestamp corresponding to current frame

        Returns:
            int: Index to current frame.
        """
        return self._ms_to_frame(ms)[0]
