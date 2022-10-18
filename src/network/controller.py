import enum
import logging
import os
from typing import List, Tuple

import numpy as np
import torch

from src.media.media_types import MediaType, media_type_of
import src.network.LARa.lara_specifics as lara_util
from src.network.network import Network
from src.utility.filehandler import Paths
from src.utility.mocap_reader import load_mocap

__network_dict__ = {}


class NetworkType(enum.Enum):
    LARA_ATTR = 0
    LARA_ATTR_CNN_IMU = 1


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


__cached_data__ = {}


def __get_data__(file: os.PathLike) -> Tuple[np.ndarray, MediaType]:
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


def __run_network__(file: os.PathLike, start: int = 0, end: int = -1) -> np.ndarray:

    # load data
    data, media_type = __get_data__(file)

    logging.info(f"{media_type = }, {data.shape = }")

    # select compatible networks
    network, config = __load_network__(media_type)
    logging.info(f"{config = }")

    # for segmentation
    segment_size = config.get("sliding_window_length")
    assert isinstance(segment_size, int) and segment_size > 0
    logging.info(f"{segment_size = }")

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
            assert end - start >= segment_size

        data = data[start:end]

        # select data in the specified interval
        logging.info(f"After data filter {start = }, {end = }: {data.shape = }")

    # input-frame is too large
    # -> pick the most middle segment as a representation of the whole frame
    if data.shape[0] > segment_size:
        logging.info(
            f"{data.shape = } is too large for the network -> reduction needed"
        )
        mid = data.shape[0] // 2
        lo = mid - segment_size // 2
        logging.debug(f"{lo = }, {mid = }, {lo + segment_size = }")
        data = data[lo : lo + segment_size]

    assert data.shape[0] == segment_size, f"{data.shape = }, {segment_size = }"

    y = __forward__(data, network)

    return y


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
        path_networks = Paths.instance().networks

        lara_paths = [
            "attrib_network.pt",
            "cnn_imu_attrib_network.pt",
            "cnn_attrib_network.pt",
        ]
        lara_paths = [os.path.join(path_networks, x) for x in lara_paths]
        network_paths = list(filter(os.path.isfile, lara_paths))

        if network_paths:
            network_path = network_paths[0]
            logging.debug(f"picked: {network_path = }")
        else:
            raise FileNotFoundError("Could not find any LARa-Network")
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
        if media_type == MediaType.LARA_MOCAP:
            return __load_lara_network__(network_path)
        elif media_type == MediaType.VIDEO:
            raise NotImplementedError
        else:
            raise ValueError(f"{media_type = } does not support a network")


def __load_lara_network__(network_path: os.PathLike) -> Tuple[Network, dict]:
    try:
        checkpoint = torch.load(network_path, map_location=torch.device("cpu"))

        state_dict = checkpoint["state_dict"]
        config = checkpoint["network_config"]

        # TODO Remove this hack
        config["fully_convolutional"] = "FC"

        network = Network(config)
        network.load_state_dict(state_dict)
        network.eval()

        # cache results
        __cached_network__["network_path"] = network_path
        __cached_network__["network"] = network
        __cached_network__["config"] = config

        return network, config
    except Exception:
        raise


def __load_video_network(network_path: os.PathLike) -> Tuple[Network, dict]:
    try:
        pass
    except Exception:
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

    data = lara_util.normalize(data)
    return data


def __postprocess__(data: np.ndarray, media_type: MediaType) -> np.ndarray:
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
    output_tensor: torch.Tensor = network(input_tensor)
    output_array = output_tensor.detach().numpy()
    return output_array.flatten()


if __name__ == "__main__":
    data_path = r"C:\Users\Raphael\Desktop\L01_S14_R01.csv"
    # data_path = r"C:\Users\Raphael\Desktop\L01_S01_R01_norm_data.csv"

    update_file(data_path)

    # run_network(0, 1000)

    network, cfg = __load_network__(MediaType.LARA_MOCAP)

    input_vec = torch.randn(1, 1, 200, 126)
    print("input_vec", input_vec)

    out = network(input_vec)
    print(out)

    print()

    print("input_vec", input_vec)
    out = network(input_vec)
    print(out)
