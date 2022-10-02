from dataclasses import dataclass, field
from src.data_classes import Annotation


@dataclass(unsafe_hash=True, order=True)
class Interval:
    _sort_index: int = field(init=False, repr=False)
    start: int = field(hash=True, compare=True)
    end: int = field(hash=True, compare=True)
    annotation: Annotation = field(hash=False, compare=False)
    similarity: float = field(hash=False, compare=False)

    def __post_init__(self):
        self._sort_index = self.start
