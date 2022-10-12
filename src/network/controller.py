import enum
import os
from typing import List, Tuple, Union

import numpy as np
import torch

from src.media.media_types import MediaType, media_type_of
from src.network.network import Network
from src.utility.mocap_reader import load_mocap


class NetworkType(enum.Enum):
    LARA_ATTR = 0
    LARA_ATTR_CNN_IMU = 1


def run_network(
    network_type: NetworkType,
    data: Union[os.PathLike, np.ndarray, torch.Tensor],
    start: int = None,
    end: int = None,
) -> Union[np.ndarray, List[np.ndarray]]:
    network = load_network(network_type)

    data, media_type = load_raw_data(data, start, end)

    data = preprocess_data(data, media_type)

    segment_size = 200
    step = 200
    data, intervals = segment_data(data, segment_size, step)

    res = []
    for seg, i in zip(data, intervals):
        y = network(seg)
        res.append((i, y))
        print(i, y)

    return res


def load_raw_data(
    data: Union[os.PathLike, np.ndarray, torch.Tensor],
    start: int = None,
    end: int = None,
) -> Tuple[np.ndarray, MediaType]:
    if isinstance(data, np.ndarray):
        return data, MediaType.UNKNOWN
    elif isinstance(data, (os.PathLike, str)):
        file = data
        if os.path.isfile(file):
            media_type = media_type_of(file)
            if media_type == MediaType.LARA_MOCAP:
                data = load_mocap(file, normalize=False)
            elif media_type == MediaType.VIDEO:
                raise NotImplementedError
            else:
                data = None

            return data, media_type
        else:
            raise
    else:
        raise


def load_network(network_type: NetworkType) -> Tuple[Network, dict]:
    try:
        checkpoint = torch.load(r"C:\Users\Raphael\Desktop\attrib_network.pt")

        state_dict = checkpoint["state_dict"]
        config = checkpoint["network_config"]

        network = Network(config)
        network.load_state_dict(state_dict)
        print(network)

        return network, config
    except:
        pass


def preprocess_data(data, media_type: MediaType = None) -> np.ndarray:
    if media_type:
        if media_type == MediaType.LARA_MOCAP:
            data = preprocess_lara(data)

    return data


def preprocess_lara(data) -> np.ndarray:
    data = np.delete(data, range(66, 72), 1)

    # TODO normalize

    return data


# TODO
def segment_data(data, segment_size, step):
    segments = []
    intervals = []

    lo = 0

    while lo + segment_size < len(data):
        hi = lo + segment_size
        seg = data[lo:hi]
        interval = (lo, hi - 1)

        segments.append(seg)
        intervals.append(interval)

        lo += step

    return segments, intervals


def forward(data_segment: np.ndarray, network: Network) -> np.ndarray:
    input_tensor = torch.from_numpy(data_segment[np.newaxis, np.newaxis, :, :]).float()
    output_tensor: torch.Tensor = network(input_tensor)
    output_array = output_tensor.detach().numpy()
    return output_array.flatten()


if __name__ == "__main__":
    data_path = r"C:\Users\Raphael\Desktop\L01_S14_R01 - Kopie.csv"
    data_path = r"C:\Users\Raphael\Desktop\L01_S01_R01_norm_data.csv"

    data, media_type = load_raw_data(data_path)
    print(1, data.shape)

    data = preprocess_data(data, media_type)
    print(2, data.shape)

    segments, intervals = segment_data(data, 200, 200)
    # print(3, segments, intervals)

    network, config = load_network(NetworkType.LARA_ATTR)
    print(network)

    for seg, i in zip(segments, intervals):
        out = forward(seg, network)
        print(i, out)
