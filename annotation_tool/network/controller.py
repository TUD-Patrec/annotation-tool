from functools import lru_cache
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch

from annotation_tool.data_model.media_type import MediaType, from_str
from annotation_tool.data_model.model import Model, get_models
from annotation_tool.media_reader import MediaReader, media_reader
from annotation_tool.utility.decorators import accepts, returns

_state = {}


@accepts(Path, int)
def update_state(file: Path, num_labels: int):
    _state["file"] = file
    _state["num_labels"] = num_labels


@returns(np.ndarray)
@accepts(int, int)
def run_network(lower: int, upper: int) -> np.ndarray:
    """
    Runs the network on the current data file and returns the output.

    Args:
        lower (int): The lower bound of the data to be processed.
        upper (int): The upper bound of the data to be processed.

    Returns:
        np.ndarray: The output of the network.

    """
    path = _state["file"]
    num_labels = _state["num_labels"]
    assert path is not None, "Path must not be None."
    assert isinstance(num_labels, int), "num_labels must be of type int."
    return __run_network__(path, lower, upper, num_labels)


@lru_cache(maxsize=1)
def __get_media_reader__(file: Path) -> MediaReader:
    return media_reader(file)


def __get_model__(mr: MediaReader, num_labels: int) -> Model:
    # find best fitting network
    media_type: str = mr.media_type
    media_type: MediaType = from_str(media_type)
    compatible_networks: List[Model] = get_models(media_type)

    media_duration: float = mr.duration / 1000  # in seconds
    media_dim = mr[0].shape

    res = []

    for model in compatible_networks:
        model_duration = model.input_shape[0] / model.sampling_rate  # in seconds
        model_dim = model.input_shape[1:]

        output_matches = model.output_size == num_labels

        input_matches = model_duration < media_duration and len(media_dim) == len(
            model_dim
        )

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

        if input_matches and output_matches:
            res.append(model)

    return res[0] if len(res) > 0 else None


def __run_network__(file: Path, start: int, end: int, num_labels: int) -> np.ndarray:
    assert os.path.isfile(file), f"{file = } is not a file"
    assert start >= 0, f"{start = } must be >= 0"
    assert end >= 0, f"{end = } must be >= 0"
    assert start <= end, f"{start = } must be <= {end = }"

    # load data
    mr = __get_media_reader__(file)

    assert len(mr) > 0, f"{len(mr) = } must be > 0"
    assert end <= len(mr), f"{end = } must be <= {len(mr) = }"

    # select compatible networks
    model = __get_model__(mr, num_labels)

    if model is None:
        raise RuntimeError("No compatible network found.")

    # for segmentation
    window_size = model.input_shape[0]
    assert isinstance(window_size, int) and window_size > 0
    assert window_size <= len(mr), f"{window_size = } is bigger than {len(mr) = }"

    # collect relevant information
    mr_fps: float = mr.fps
    model_fps: int = model.sampling_rate
    step_size: float = mr_fps / model_fps

    # compute middle frame
    middle_frame: int = (start + end) // 2

    # find good starting frame
    start_frame: float = middle_frame - (step_size * window_size / 2)
    start_frame: int = int(start_frame)

    indices = []
    for i in range(window_size):
        idx = int(start_frame + i * step_size)
        indices.append(idx)

    indices = np.array(indices).astype(int)
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

    data = [mr[idx.item()] for idx in indices]
    data = np.array(data)

    y = __forward__(data, model)

    # print(
    #    f"{delta_time = :.2f} -> {_mr_delta_time = :.2f} | {_seg_delta_time = :.2f} | {_data_load_delta_time = :.2f} | {_network_delta_time = :.2f}"
    # )
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

    output_array: np.ndarray = output_tensor.numpy(force=True)
    return output_array.flatten()
