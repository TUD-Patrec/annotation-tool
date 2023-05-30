from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path
import time
from typing import List, Optional, Tuple

import torch

from annotation_tool.data_model.media_type import MediaType
from annotation_tool.file_cache import cached
from annotation_tool.utility.filehandler import checksum


def get_unique_name() -> str:
    taken_names = [m.name for m in Model.get_all()]

    # find string of form "Model_#" that is not taken
    i = 0
    while True:
        name = f"Model_{i}"
        if name not in taken_names:
            return name
        i += 1


@lru_cache(maxsize=1)
def load_network(path: Path, expected_hash: str, allow_cuda: bool):
    computed_hash = checksum(path, fast_hash=True)
    if computed_hash is None or computed_hash != expected_hash:
        raise RuntimeError(
            f"The file {path} has an unexpected hash. Expected {expected_hash} but got {computed_hash}."
        )
    if allow_cuda and torch.cuda.is_available():
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device("cpu")
    try:
        model = torch.load(path, map_location=device)
    except Exception as e:
        raise RuntimeError(f"Loading the network from location {path} failed.") from e
    return model


@cached
@dataclass
class Model:
    """
    Wrapper for storing metadata about neural network models.
    """

    network_path: Path
    media_type: MediaType
    sampling_rate: int
    input_shape: Tuple[int, ...]
    output_size: int
    name: str = field(init=True, default=None)
    activated: bool = field(init=False, default=True)
    _checksum: str = field(init=False)
    size_bytes: int = field(init=False, default=0)
    creation_time: time.struct_time = field(init=False, default=None)

    def __post_init__(self):
        self.size_bytes = os.path.getsize(self.network_path)
        self._checksum = checksum(self.network_path, fast_hash=True)
        self.creation_time = time.localtime(os.path.getctime(self.network_path))
        if self.name is None:
            self.name = get_unique_name()

    @property
    def path(self):
        return self.network_path

    @property
    def timestamp(self) -> str:
        return time.strftime("%Y-%m-%d_%H-%M-%S", self.creation_time)

    @property
    def checksum(self) -> str:
        return self._checksum

    def load(self, allow_cuda: bool = False) -> torch.nn.Module:
        """
        Loads the network from disk.

        Args:
            allow_cuda: Whether to allow CUDA usage.
        Returns:
            The loaded network.
        """
        return load_network(self.network_path, self.checksum, allow_cuda)


def create_model(
    network_path: Path,
    media_type: MediaType,
    sampling_rate: int,
    input_shape: Tuple[int, ...],
    output_size: int = None,
    name: str = None,
) -> Model:
    """
    Creates a new Model object and writes it to the cache.

    Args:
        network_path: The path to the network file.
        media_type: The media type of the network.
        sampling_rate: The sampling rate (FPS) of the network [1/s].
        input_shape: The input shape of the network.
        output_size: The number of output classes of the network. If None, this will be inferred by running the network once.
        name: The name of the network. If None, a unique name will be generated.
    Returns:
        The new Model object.
    """
    # try to load network and check if it is valid
    try:
        network = torch.load(network_path, map_location="cpu")
    except Exception as e:
        raise RuntimeError(
            f"Loading the network from location {network_path} failed."
        ) from e

    network.eval()
    _sample_shape = [x if isinstance(x, int) else x[0] for x in input_shape]
    sample_input = torch.randn(1, *_sample_shape)
    try:
        with torch.no_grad():
            out = network(sample_input)
    except Exception as e:
        raise ValueError(
            f"The network at {network_path} does not accept input of shape {input_shape}"
        ) from e

    assert (
        len(out.shape) == 2
    ), f"The network is expected to return a (B, C) tensor. Got a tensor of shape {out.shape}"

    if output_size is None:
        output_size = out.shape[1]  # infer from network output

    if output_size != out.shape[1]:
        error_str = (
            f"Network output shape mismatch. Expected {output_size}, got {out.shape[1]}"
        )
        raise ValueError(error_str)

    return Model(
        network_path, media_type, sampling_rate, input_shape, output_size, name
    )


def get_models(media_type: MediaType, get_deactivated=False) -> List[Model]:
    """
    Returns all models of a certain media type.

    Args:
        media_type: The media type to filter by.
        get_deactivated: Whether to return deactivated models.
    Returns:
        A list of models.
    """
    return [
        m
        for m in Model.get_all()
        if (m.media_type == media_type and (m.activated or get_deactivated))
    ]


def get_model_by_mediatype(media_type: MediaType) -> Optional[Model]:
    """
    Returns the first model of a certain media type.

    Args:
        media_type: The media type to filter by.
    Returns:
        The first model of the media type. None if no model exists.
    """
    models = get_models(media_type)
    if len(models) > 0:
        return models[0]
    return None
