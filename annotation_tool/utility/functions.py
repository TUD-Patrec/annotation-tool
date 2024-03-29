import functools
from typing import Tuple


def scale(N: int, M: int, x: int) -> Tuple[int, int]:
    """
    Scaling function that scales some point x within a range
    of N elements to another range of M elements while keeping its
    relative position inside that range.
    Scaling from some smaller range to a bigger one maps one point
    into an element of possibly multiple-points.
    Args:
        N (int): Size of the initial range.
        M (int): Size of the new range.
        x (int): Point inside the initial range that will be mapped.

    Raises:
        ValueError: Raised if any of the input-values is not an integer.

    Returns:
        Tuple[int, int]: Closed element in the new range where the
        initial point is mapped onto.
    """
    if isinstance(N, int) and isinstance(M, int) and isinstance(x, int):
        if N == M:
            return x, x
        if N > M:
            return (x * M) // N, (x * M) // N
        if N < M:
            if N > 0:
                lo = (x * M) // N if (x * M) % N == 0 else (x * M) // N + 1
                hi = (
                    ((x + 1) * M) // N - 1
                    if ((x + 1) * M) % N == 0
                    else ((x + 1) * M) // N
                )
            else:
                lo, hi = 0, M - 1
            return lo, hi
    raise ValueError


def scale_functions(N: int, M: int, last_to_last: bool = False):
    """
    Create scaling functions

    Args:
        N (int): Number of elements in the first range.
        M (int): Number of elements in the second range.
        last_to_last (bool, optional): Sometimes it's useful if the last elements
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
    """
    Create a human readable representation for the given milliseconds.

    Args:
        ms (int): Milliseconds.

    Returns:
        str: String representation formatted as mm:ss:mmm.
    """
    mins = ms // (60 * 1000)
    ms %= 60 * 1000
    secs = ms // 1000
    ms %= 1000
    return "{:02d}:{:02d}:{:03d}".format(mins, secs, ms)
