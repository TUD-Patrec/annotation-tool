from dataclasses import dataclass
from typing import List

import numpy as np

from . import AnnotationScheme
from ..utility.file_cache import Cachable


@dataclass()
class Dataset(Cachable):
    name: str
    scheme: AnnotationScheme
    dependencies: List[np.ndarray]

    def __post_init__(self):
        super().__init__()
