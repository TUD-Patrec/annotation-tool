from copy import deepcopy
from dataclasses import dataclass, field

from src.data_classes import Annotation, Sample


@dataclass(unsafe_hash=True, order=True)
class Interval:
    _sort_index: int = field(init=False, repr=False, compare=False)
    start: int = field(hash=True, compare=True)
    end: int = field(hash=True, compare=True)
    annotation: Annotation = field(hash=True, compare=False)
    similarity: float = field(hash=True, compare=False)

    def __post_init__(self):
        self._sort_index = self.start

    def as_sample(self):
        anno = deepcopy(self.annotation)
        sample = Sample(self.start, self.end, anno)
