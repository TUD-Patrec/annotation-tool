from dataclasses import dataclass, field
import os

from src.media import MediaType, media_type_of
from src.utility.file_cache import cached


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
    input_shape: tuple
    output_shape: tuple
    media_type: MediaType = field(init=False)
    name: str = field(init=True, default=get_unique_name())
    size_bytes: int = field(init=False, default=0)
    preprocessing_script_path: os.PathLike = field(init=False, default=None)

    def __post_init__(self):
        self.size_bytes = os.path.getsize(self.network_path)
        self.media_type = media_type_of(self.network_path)
