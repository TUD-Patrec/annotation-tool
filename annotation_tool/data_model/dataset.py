from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from annotation_tool.file_cache import cached

from .annotation_scheme import AnnotationScheme


@cached
@dataclass
class Dataset:
    _name: str = field(init=True)
    _scheme: AnnotationScheme = field(init=True)
    _dependencies: np.ndarray = field(init=True, default=None, compare=False)

    def __post_init__(self):
        assert self.name is not None, "Name must not be None."
        assert isinstance(self.name, str), "Name must be of type str."
        assert len(self.name) > 0, "Name must not be empty."
        assert self.scheme is not None, "Scheme must not be None."
        assert isinstance(
            self.scheme, AnnotationScheme
        ), "Scheme must be of type AnnotationScheme."
        if self.dependencies is not None:
            assert self.dependencies is not None, "Dependencies must not be None."
            assert isinstance(
                self.dependencies, np.ndarray
            ), "Dependencies must be of type np.ndarray."

    @property
    def name(self) -> str:
        return self._name

    @property
    def scheme(self) -> AnnotationScheme:
        return self._scheme

    @property
    def dependencies(self) -> np.ndarray:
        return self._dependencies

    def __copy__(self):
        return Dataset(self.name, self.scheme, self.dependencies)

    def __deepcopy__(self, memo):
        return Dataset(self.name, deepcopy(self.scheme), deepcopy(self.dependencies))


def create_dataset(
    name: str, scheme: AnnotationScheme, dependencies: Optional[np.ndarray] = None
) -> Dataset:
    """
    Creates a new dataset with the given name and annotation scheme.

    Args:
        name: The name of the dataset.
        scheme: The annotation scheme of the dataset.
        dependencies: The dependencies of the dataset.

    Returns:
        The created dataset.

    Raises:
        ValueError: If the parameters are invalid.
    """
    try:
        return Dataset(name, scheme, dependencies)
    except AssertionError as e:
        raise ValueError(e)
