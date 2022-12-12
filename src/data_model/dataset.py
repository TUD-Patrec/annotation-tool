from dataclasses import dataclass, field

import numpy as np

from src.utility.file_cache import cached

from .annotation_scheme import AnnotationScheme


@cached
@dataclass
class Dataset:
    _name: str = field(init=True)
    _scheme: AnnotationScheme = field(init=True)
    _dependencies: np.ndarray = field(init=True, default=None, compare=False)

    @property
    def name(self) -> str:
        return self._name

    @property
    def scheme(self) -> AnnotationScheme:
        return self._scheme

    @property
    def dependencies(self) -> np.ndarray:
        return self._dependencies
