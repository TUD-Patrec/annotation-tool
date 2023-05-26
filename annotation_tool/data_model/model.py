from dataclasses import dataclass, field
import os
import time
from typing import List, Optional, Tuple

import torch

from annotation_tool.data_model.media_type import MediaType
from annotation_tool.file_cache import cached
from annotation_tool.utility.filehandler import footprint_of_file


def get_unique_name() -> str:
    taken_names = [m.name for m in Model.get_all()]

    # find string of form "Model_#" that is not taken
    i = 0
    while True:
        name = f"Model_{i}"
        if name not in taken_names:
            return name
        i += 1


@cached
@dataclass
class Model:
    """
    Wrapper for storing metadata about neural network models.
    """

    network_path: os.PathLike
    media_type: MediaType
    sampling_rate: int
    input_shape: Tuple[int, ...] = field(init=True)
    output_shape: Tuple[int, ...] = field(init=True, default=None)
    name: str = field(init=True, default=None)
    activated: bool = field(init=False, default=True)
    footprint: int = field(init=False)
    basename: str = field(init=False)
    size_bytes: int = field(init=False, default=0)
    creation_time: time.struct_time = field(
        init=False, default_factory=lambda: time.localtime
    )
    correct_classifications: int = field(init=False, default=0)
    incorrect_classifications: int = field(init=False, default=0)

    def __post_init__(self):
        self.size_bytes = 0  # placeholder for now -> later something like: os.path.getsize(self.network_path)
        self.basename = os.path.basename(self.network_path)
        self.footprint = footprint_of_file(self.network_path, fast_hash=True)
        if self.name is None:
            self.name = get_unique_name()

        # try to load network and check if it is valid
        try:
            network = self.load()
        except Exception as e:
            raise Exception(
                f"Network at {self.network_path} could not be loaded."
            ) from e

        network.eval()
        sample_input = torch.randn(1, *self.input_shape)
        try:
            out = network(sample_input)
        except Exception as e:
            raise Exception(
                f"Network at {self.network_path} could not be evaluated."
            ) from e

        if self.output_shape is None:
            self.output_shape = tuple(out.shape[1:])

        if self.output_shape != out.shape[1:]:
            error_str = f"Network output shape mismatch. Expected {self.output_shape}, got {out.shape[1:]}"
            raise RuntimeError(error_str)

    @property
    def path(self):
        return self.network_path

    @property
    def timestamp(self) -> str:
        return time.strftime("%Y-%m-%d_%H-%M-%S", self.creation_time)

    @property
    def accuracy(self) -> float:
        return self.correct_classifications / (
            self.correct_classifications + self.incorrect_classifications
        )

    @property
    def n_predictions(self) -> int:
        return self.correct_classifications + self.incorrect_classifications

    def reset(self):
        self.correct_classifications = 0
        self.incorrect_classifications = 0

    def load(self, allow_cuda: bool = False) -> torch.nn.Module:
        """
        Loads the network from disk.

        Args:
            allow_cuda: Whether to allow CUDA usage.
        Returns:
            The loaded network.
        """
        if allow_cuda and torch.cuda.is_available():
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device = torch.device("cpu")
        model = torch.load(self.network_path, map_location=device)
        model.eval()
        return model


def create_model(
    network_path: os.PathLike,
    media_type: MediaType,
    sampling_rate: int,
    input_shape: Tuple[int, ...],
    output_shape: Tuple[int, ...] = None,
    name: str = None,
) -> Model:
    """
    Creates a new Model object and writes it to the cache.

    Args:
        network_path: The path to the network file.
        media_type: The media type of the network.
        sampling_rate: The sampling rate (FPS) of the network [1/s].
        input_shape: The input shape of the network.
        output_shape: The output shape of the network. If None, it will be inferred from the network.
        name: The name of the network. If None, a unique name will be generated.
    Returns:
        The new Model object.
    """
    return Model(
        network_path, media_type, sampling_rate, input_shape, output_shape, name
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
