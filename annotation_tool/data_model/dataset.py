from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from annotation_tool.file_cache import cached

from ..utility.decorators import accepts, returns
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
    def dependencies(self) -> Optional[np.ndarray]:
        return self._dependencies


@returns(Dataset)
@accepts(str, AnnotationScheme, (np.ndarray, type(None)))
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
    return Dataset(name, scheme, dependencies)
