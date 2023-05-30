from functools import lru_cache
import os
from pathlib import Path
import time
from typing import List, Tuple

import numpy as np
import torch

from annotation_tool.data_model.media_type import MediaType, from_str
from annotation_tool.data_model.model import Model, get_models
from annotation_tool.media_reader import MediaReader, media_reader

_state_ = {
    "file": None,
    "num_labels": None,
}


def update_state(file: Path, num_labels: int):
    _state_["file"] = file
    _state_["num_labels"] = num_labels
    print(f"Updated state: {_state_}")


def run_network(lower: int, upper: int) -> np.ndarray:
    """
    Runs the network on the current data file and returns the output.

    Args:
        lower (int): The lower bound of the data to be processed.
        upper (int): The upper bound of the data to be processed.

    Returns:
        np.ndarray: The output of the network.

    """
    path = _state_["file"]
    num_labels = _state_["num_labels"]
    assert path is not None, "Path must not be None."
    assert isinstance(num_labels, int), "num_labels must be of type int."
    return __run_network__(path, lower, upper, num_labels)


@lru_cache(maxsize=1)
def __get_media_reader__(file: Path) -> MediaReader:
    return media_reader(file)


@lru_cache(maxsize=1)
def __get_model__(mr: MediaReader, num_labels: int) -> Model:
    # find best fitting network
    media_type: str = mr.media_type
    media_type: MediaType = from_str(media_type)
    compatible_networks: List[Model] = get_models(media_type)

    print(
        f"Found {len(compatible_networks)}networks with same media-type: {compatible_networks}"
    )

    media_duration: float = mr.duration / 1000  # in seconds
    media_dim = mr[0].shape

    res = []

    for model in compatible_networks:
        model_duration = model.input_shape[0] / model.sampling_rate  # in seconds
        model_dim = model.input_shape[1:]

        print(
            f"{media_duration = } | {media_dim = } | {model_duration = } | {model_dim = }"
        )

        output_matches = model.output_size == num_labels
        print(f"Output matches: {output_matches}")

        input_matches = model_duration < media_duration and len(media_dim) == len(
            model_dim
        )
        print(f"Input matches: {input_matches} (before loop)")

        for i, s in enumerate(model_dim):
            s_other = media_dim[i]
            if isinstance(s, tuple):
                s_min, s_max = s
                s_max = np.inf if s_max == -1 else s_max

                input_matches = input_matches and s_min <= s_other <= s_max
            elif isinstance(s, int):
                input_matches = input_matches and s == s_other
            else:
                raise TypeError(f"Unknown type: {type(s)}")

        print(f"Input matches: {input_matches} (after loop)")
        if input_matches and output_matches:
            res.append(model)

    print(f"Found {len(res)} compatible networks:", *res, sep="\n\t")

    return res[0] if len(res) > 0 else None


def __run_network__(file: Path, start: int, end: int, num_labels: int) -> np.ndarray:
    start_time = time.perf_counter()

    assert os.path.isfile(file), f"{file = } is not a file"
    assert start >= 0, f"{start = } must be >= 0"
    assert end >= 0, f"{end = } must be >= 0"
    assert start <= end, f"{start = } must be <= {end = }"

    # load data
    _mr_start_time = time.perf_counter()
    mr = __get_media_reader__(file)
    _mr_end_time = time.perf_counter()
    _mr_delta_time = _mr_end_time - _mr_start_time

    assert len(mr) > 0, f"{len(mr) = } must be > 0"
    assert end <= len(mr), f"{end = } must be <= {len(mr) = }"

    # select compatible networks
    model = __get_model__(mr, num_labels)

    if model is None:
        raise RuntimeError("No compatible network found.")

    _seg_start_time = time.perf_counter()
    # for segmentation
    window_size = model.input_shape[0]
    assert isinstance(window_size, int) and window_size > 0
    assert window_size <= len(mr), f"{window_size = } is bigger than {len(mr) = }"

    # collect relevant information
    mr_fps: float = mr.fps
    model_fps: int = model.sampling_rate
    step_size: float = mr_fps / model_fps
    # print(f"{mr_fps = } | {model_fps = } | {step_size = }")

    # compute middle frame
    middle_frame: int = (start + end) // 2

    # find good starting frame
    start_frame: float = middle_frame - (step_size * window_size / 2)
    start_frame: int = int(start_frame)
    # print(f"{start_frame = }")

    # compute end frame
    end_frame: float = start_frame + (step_size * window_size)
    end_frame: int = int(end_frame)
    # print(f"{end_frame = }")

    indices = []
    for i in range(window_size):
        idx = int(start_frame + i * step_size)
        indices.append(idx)

    indices = np.array(indices).astype(int)
    # print(f"{indices = }")
    # print(f"{indices.shape = }")
    min_idx, max_idx = indices.min(), indices.max()

    # check bounds
    if min_idx < 0:
        indices -= min_idx
        assert indices.min() == 0 and indices.max() < len(
            mr
        ), f"{indices.min() = } | {indices.max() = } | {len(mr) = }"
    elif max_idx >= len(mr):
        indices -= max_idx - len(mr) + 1
        assert (
            indices.min() >= 0 and indices.max() == len(mr) - 1
        ), f"{indices.min() = } | {indices.max() = } | {len(mr) = }"

    assert (
        0 <= indices.min() <= middle_frame <= indices.max() < len(mr)
    ), f"{indices.min() = } | {middle_frame = } | {indices.max() = } | {len(mr) = }"
    # print(f"After boundary-checking: {indices = }")

    start_frame = indices.min()
    end_frame = indices.max() + 1
    print(
        f"{mr.fps = } | {model.sampling_rate = } | {start_frame = } | {middle_frame = } | {end_frame = } | {step_size = :.2f} | {window_size = } | {len(mr) = }"
    )

    _seg_end_time = time.perf_counter()
    _seg_delta_time = _seg_end_time - _seg_start_time

    # read data
    # print(f"{indices.shape = }")
    # indices = indices.flatten().tolist()
    # print(f"{indices = }")
    _data_load_start_time = time.perf_counter()
    data = [mr[idx.item()] for idx in indices]
    data = np.array(data)
    # print(f"{data.shape = }")
    _data_load_end_time = time.perf_counter()
    _data_load_delta_time = _data_load_end_time - _data_load_start_time

    _network_start_time = time.perf_counter()
    y = __forward__(data, model)
    _network_end_time = time.perf_counter()
    _network_delta_time = _network_end_time - _network_start_time

    end_time = time.perf_counter()
    delta_time = end_time - start_time

    print(
        f"{delta_time = :.2f} -> {_mr_delta_time = :.2f} | {_seg_delta_time = :.2f} | {_data_load_delta_time = :.2f} | {_network_delta_time = :.2f}"
    )
    return y


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


def __forward__(data_segment: np.ndarray, model: Model) -> np.ndarray:
    network: torch.nn.Module = model.load()
    network.eval()

    input_tensor: torch.Tensor = torch.from_numpy(data_segment).float()
    input_tensor = input_tensor.unsqueeze(0)  # add batch dimension

    with torch.no_grad():
        output_tensor: torch.Tensor = network(input_tensor)

    output_array: np.ndarray = output_tensor.detach().numpy()
    return output_array.flatten()
