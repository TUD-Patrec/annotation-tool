from dataclasses import dataclass, field
from src.data_classes import Annotation


@dataclass(unsafe_hash=True)
class Interval:
    start: int = field(hash=True, compare=True)
    end: int = field(hash=True, compare=True)
    annotation: Annotation = field(hash=False, compare=False)
    similarity: float = field(hash=False, compare=False)
