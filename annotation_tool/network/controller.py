from functools import lru_cache
import os
from typing import List, Tuple

import numpy as np
import torch

from annotation_tool.data_model.model import Model, get_models
from annotation_tool.media_reader import MediaReader, media_reader
from annotation_tool.network.network import Network

__data_file__ = None


def update_file(file: os.PathLike) -> None:
    global __data_file__
    __data_file__ = file


def __current_data_path__() -> os.PathLike:
    global __data_file__
    return __data_file__


def run_network(lower, upper) -> np.ndarray:
    path = __current_data_path__()
    return __run_network__(path, lower, upper)


def __run_network__(file: os.PathLike, start: int = 0, end: int = -1) -> np.ndarray:
    # load data
    mr = media_reader(file)

    # select compatible networks
    model = __select_model__(mr)
    data = np.ndarray(mr[start:end])

    # for segmentation
    segment_size = model.input_shape[0]
    assert isinstance(segment_size, int) and segment_size > 0

    assert segment_size <= len(mr), f"{segment_size = } is bigger than {len(mr) = }"

    # mr_fps = mr.fps
    # model_fps = model.sampling_rate

    # filter element if specified
    if end >= 0:
        assert start <= end

        # additional treatment needed if the given range is too small for the network
        if end - start < segment_size:
            # how many elements need to be added to have the correct array size
            delta = segment_size - (end - start)
            left_delta = delta // 2
            right_delta = delta - left_delta

            # lower bound
            if start - left_delta < 0:
                left_delta = start  # start - 0 == start
                right_delta = delta - left_delta
            # upper bound
            elif end + right_delta >= data.shape[0]:
                right_delta = (data.shape[0] - 1) - end
                left_delta = delta - right_delta
            start -= left_delta
            end += right_delta

        # some consistency checks
        assert (
            0 <= start <= end <= data.shape[0]
        ), f"{start = }, {end = }, {data.shape[0] = }"
        assert end - start >= segment_size

        data = data[start:end]

        # select data in the specified element
        # logging.info(f"After data filter {start = }, {end = }: {data.shape = }")

    # input-frame is too large
    # -> pick the most middle segment as a representation of the whole frame
    if data.shape[0] > segment_size:
        # logging.info(
        #     f"{data.shape = } is too large for the network -> reduction needed"
        # )
        mid = data.shape[0] // 2
        lo = mid - segment_size // 2
        data = data[lo : lo + segment_size]

    assert data.shape[0] == segment_size, f"{data.shape = }, {segment_size = }"

    network = None
    y = __forward__(data, network)

    return y


@lru_cache(maxsize=1)
def __select_model__(media_reader: MediaReader) -> Model:
    # find best fitting network

    compatible_networks = get_models(media_reader.media_type)
    return compatible_networks[0]


def __segment_data__(
    data: np.ndarray, segment_size: int, step: int
) -> Tuple[List[np.ndarray], List[tuple]]:
    segments = []
    intervals = []

    lo = 0

    while lo + segment_size < data.shape[0]:
        hi = lo + segment_size
        seg = data[lo:hi]
        interval = (lo, hi)

        segments.append(seg)
        intervals.append(interval)

        lo += step

    if lo < data.shape[0]:
        tmp = data.shape[0] - segment_size
        seg = data[tmp : data.shape[0]]
        interval = (tmp, data.shape[0])

        segments.append(seg)
        intervals.append(interval)

    return segments, intervals


def __forward__(data_segment: np.ndarray, network: Network) -> np.ndarray:
    input_tensor = torch.from_numpy(data_segment[np.newaxis, np.newaxis, :, :]).float()
    output_tensor: torch.Tensor = network(input_tensor)
    output_array = output_tensor.detach().numpy()
    return output_array.flatten()
