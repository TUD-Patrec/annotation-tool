import enum
import logging
import os
import time
from typing import List, Tuple, Union

import numpy as np
import torch

from src.media.media_types import MediaType, media_type_of
from src.network.network import Network
from src.utility.mocap_reader import load_mocap


class NetworkType(enum.Enum):
    LARA_ATTR = 0
    LARA_ATTR_CNN_IMU = 1


data_file = None


def update_file(file: os.PathLike):
    global data_file
    data_file = file


def __current_data_path__():
    global data_file
    return data_file


def run_network(lower, upper):
    path = __current_data_path__()
    return __run_network__(path, lower, upper)


__cached_data__ = {}


def __get_data__(file):
    media_type = media_type_of(file)

    cached_media_type = __cached_data__.get("media_type")
    if cached_media_type and cached_media_type == media_type:
        # data already loaded
        data = __cached_data__.get("data")
        assert data is not None
    else:
        # load from disk
        data = __load_raw_data__(file, media_type)

        # preprocess
        data = __preprocess_data__(data, media_type)

        # cache data
        __cached_data__["media_type"] = media_type
        __cached_data__["data"] = data

    return data, media_type


def __run_network__(
    file: os.PathLike, start: int = 0, end: int = -1
) -> Union[List[np.ndarray], np.ndarray]:

    # load data
    data, media_type = __get_data__(file)

    logging.info(f"{media_type = }, {data.shape = }")
    # print(f'{media_type = }, {data.shape = }')

    # select compatible networks
    network, config = __load_network__(media_type)
    logging.info(f"{config = }")
    # print(f"{config = }")

    # for segmentation
    segment_size = config.get("sliding_window_length")
    assert isinstance(segment_size, int) and segment_size > 0
    logging.info(f"{segment_size = }")
    # print(f"{segment_size = }")

    # make sure the data is segmentable
    assert (
        segment_size <= data.shape[0]
    ), f"{segment_size = } is bigger than {data.shape[0] = }"

    # filter interval if specified
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
            assert 0 <= start <= end < data.shape[0], f"{start = }, {end = }"
            assert end - start == segment_size

        # select data in the specified interval
        data = data[start:end]

    logging.info(f"After data filter {start = }, {end = }: {data.shape = }")
    # print(f"After data filter: {data.shape = }")

    # segment data
    step = segment_size
    data, intervals = __segment_data__(data, segment_size, step)

    logging.info(f"{intervals = }")
    # print(f"{intervals = }")

    # run network for each segment
    res = []
    for seg, i in zip(data, intervals):
        y = __forward__(seg, network)
        res.append((i, y))
        print(i, y)

    if len(res) == 1:
        y = res[0][1]
        logging.info(f"Single result: {y = }")
        # print(f'Single result: {y = }')
        return y
    else:
        return res


def __load_raw_data__(file: os.PathLike, media_type: MediaType = None) -> np.ndarray:
    if media_type is None:
        media_type = media_type_of(file)

    if media_type == MediaType.LARA_MOCAP:
        data = load_mocap(file, normalize=False)
    elif media_type == MediaType.VIDEO:
        raise NotImplementedError
    else:
        data = None

    return data


__cached_network__ = {}


def __load_network__(media_type: MediaType) -> Tuple[Network, dict]:
    # find best fitting network

    if media_type == MediaType.LARA_MOCAP:
        network_path = r"C:\Users\Raphael\Desktop\attrib_network.pt"
        # network_path = r"C:\Users\Raphael\Desktop\cnn_imu_attrib_network.pt"
        # network_path = r"C:\Users\Raphael\Desktop\cnn_attrib_network.pt"
    elif media_type == MediaType.VIDEO:
        raise NotImplementedError
    else:
        raise ValueError(f"{media_type = } is not usable.")

    cached_network_path = __cached_network__.get("network_path")
    if cached_network_path and cached_network_path == network_path:
        network = __cached_network__.get("network")
        assert network is not None
        config = __cached_network__.get("config")
        return network, config
    else:
        try:
            checkpoint = torch.load(network_path, map_location=torch.device("cpu"))

            state_dict = checkpoint["state_dict"]
            config = checkpoint["network_config"]

            # TODO Remove this hack
            config["fully_convolutional"] = "FC"
            # print(f"{config = }")

            network = Network(config)
            network.load_state_dict(state_dict)

            # cache results
            __cached_network__["network_path"] = network_path
            __cached_network__["network"] = network
            __cached_network__["config"] = config

            return network, config
        except:
            raise


def __preprocess_data__(data, media_type: MediaType) -> np.ndarray:
    if media_type == MediaType.LARA_MOCAP:
        data = __preprocess_lara__(data)
    elif media_type == MediaType.VIDEO:
        raise NotImplementedError
    else:
        raise ValueError(f"{media_type} cannot be used for network prediction.")
    return data


def __preprocess_lara__(data) -> np.ndarray:
    data = np.delete(data, range(66, 72), 1)
    import src.network.lara_specifics as lara_util

    data = lara_util.normalize(data)
    return data


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
    output_tensor: torch.Tensor = network.forward(input_tensor)
    output_array = output_tensor.detach().numpy()
    # output_array = np.round(output_array).astype(dtype=np.int8)
    return output_array.flatten()


if __name__ == "__main__":
    # data_path = r"C:\Users\Raphael\Desktop\L01_S14_R01 - Kopie.csv"
    data_path = r"C:\Users\Raphael\Desktop\L01_S01_R01_norm_data.csv"

    # data = load_raw_data(data_path)
    # media_type = media_type_of(data_path)
    # print(1, data.shape, media_type)

    # data = preprocess_data(data, media_type)
    # print(2, data.shape)

    # segments, intervals = segment_data(data, 200, 200)
    # print(3, segments, intervals)

    # network, config = load_network(media_type)
    # print(network)

    # for seg, i in zip(segments, intervals):
    #    out = forward(seg, network)
    #    print(i, out)

    s = time.perf_counter()
    __run_network__(data_path, end=3213)
    e = time.perf_counter()
    print(f"{e - s}sec")

    s = time.perf_counter()
    __run_network__(data_path, end=3213)
    e = time.perf_counter()
    print(f"{e - s}sec")

    s = time.perf_counter()
    __run_network__(data_path, end=3213)
    e = time.perf_counter()
    print(f"{e - s}sec")

    s = time.perf_counter()
    __run_network__(data_path, end=3213)
    e = time.perf_counter()
    print(f"{e - s}sec")
