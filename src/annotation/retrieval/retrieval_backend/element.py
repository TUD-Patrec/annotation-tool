from dataclasses import dataclass, field
from typing import Tuple, Union

from src.data_model import Annotation, Sample


@dataclass(eq=True, unsafe_hash=True)
class RetrievalElement:
    annotation: Annotation = field(init=True, hash=False)
    interval: Tuple[int, int] = field(init=True, hash=False)
    distance: float = field(init=True, hash=True)
    i: int = field(init=True, hash=True)  # element index
    j: Union[int, None] = field(init=True, hash=True)  # attribute representation index

    def as_sample(self) -> Sample:
        """Converts the retrieval element to a sample."""
        return Sample(self.interval[0], self.interval[1], self.annotation)

    @property
    def interval_index(self):
        return self.i

    @property
    def attribute_representation_index(self):
        return self.j

    @property
    def _similarity(self):
        return 1 - self.distance
