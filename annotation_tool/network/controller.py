from functools import lru_cache
import os
from typing import List, Tuple

import numpy as np
import torch

from annotation_tool.data_model.media_type import MediaType, from_str
from annotation_tool.data_model.model import Model, get_models
from annotation_tool.media_reader import MediaReader, media_reader

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
    assert os.path.isfile(file), f"{file = } is not a file"
    assert start >= 0, f"{start = } must be >= 0"
    assert end >= 0, f"{end = } must be >= 0"
    assert start <= end, f"{start = } must be <= {end = }"

    # load data
    mr = media_reader(file)

    assert len(mr) > 0, f"{len(mr) = } must be > 0"
    assert end < len(mr), f"{end = } must be < {len(mr) = }"

    # select compatible networks
    model = __select_model__(mr)

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
        f"{mr.fps = } | {model.sampling_rate = } | {start_frame = } | {middle_frame = } | {end_frame = } | {window_size = } | {len(mr) = }"
    )

    # read data
    # print(f"{indices.shape = }")
    # indices = indices.flatten().tolist()
    # print(f"{indices = }")
    data = [mr[idx.item()] for idx in indices]
    data = np.array(data)
    # print(f"{data.shape = }")

    y = __forward__(data, model)
    # print(f"{y.shape = }")

    return y


@lru_cache(maxsize=1)
def __select_model__(media_reader: MediaReader) -> Model:
    # find best fitting network
    media_type: str = media_reader.media_type
    media_type: MediaType = from_str(media_type)
    compatible_networks: List[Model] = get_models(media_type)
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


def __forward__(data_segment: np.ndarray, model: Model) -> np.ndarray:
    network: torch.nn.Module = model.network
    input_tensor: torch.Tensor = torch.from_numpy(
        data_segment[np.newaxis, np.newaxis, :, :]
    ).float()
    output_tensor: torch.Tensor = network(input_tensor)
    output_array: np.ndarray = output_tensor.detach().numpy()
    return output_array.flatten()
