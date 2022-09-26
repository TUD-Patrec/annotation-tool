from dataclasses import dataclass, field

import numpy as np


@dataclass(unsafe_hash=True)
class Interval:
    start: int = field(hash=True, compare=True)
    end: int = field(hash=True, compare=True)
    predicted_classification: np.ndarray = field(hash=False, compare=False)
    similarity: float = field(hash=False, compare=False)

