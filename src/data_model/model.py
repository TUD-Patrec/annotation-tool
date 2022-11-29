from dataclasses import dataclass, field
import os
import time
from typing import List, Optional

from src.media import MediaType
from src.utility.file_cache import cached
from src.utility.filehandler import footprint_of_file


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
    sampling_rate: int
    media_type: MediaType
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


def make_model(
    network_path: os.PathLike,
    sampling_rate: int,
    media_type: MediaType,
    name: str = None,
) -> Model:
    """
    Creates a new Model object and writes it to the cache.

    Args:
        network_path: The path to the network file.
        sampling_rate: The sampling rate of the network.
        media_type: The media type of the network.
        name: The name of the network. If None, a unique name will be generated.
    Returns:
        The new Model object.
    """
    return Model(network_path, sampling_rate, media_type, name)


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
