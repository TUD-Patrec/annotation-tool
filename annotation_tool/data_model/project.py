from copy import deepcopy
from dataclasses import dataclass, field

from annotation_tool.file_cache import cached
from annotation_tool.utility.decorators import accepts_m

from .annotation import Annotation
from .dataset import Dataset


@cached
@dataclass
class Project:
    name: str
    _dataset: Dataset
    _global_states: list = field(init=False, default_factory=list)

    def __post_init__(self):
        assert self.dataset is not None, "Dataset must not be None."
        assert isinstance(self.dataset, Dataset), "Dataset must be of type Dataset."
        assert self.name is not None, "Name must not be None."
        assert isinstance(self.name, str), "Name must be of type str."
        assert len(self.name) > 0, "Name must not be empty."

    @property
    def global_states(self) -> list:
        return self._global_states

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    @accepts_m(Annotation)
    def add_global_state(self, global_state: Annotation):
        if global_state.dataset != self.dataset:
            raise ValueError("GlobalState is not from the same dataset as the project.")
        self._global_states.append(global_state)

    @accepts_m(Annotation)
    def remove_global_state(self, global_state: Annotation):
        if global_state in self._global_states:
            self._global_states.remove(global_state)

    def __copy__(self):
        return Project(self.name, self.dataset, self.global_states)

    def __deepcopy__(self, memo):
        return Project(self.name, deepcopy(self.dataset), deepcopy(self.global_states))


def create_project(name: str, dataset: Dataset) -> Project:
    """
    Creates a new project with the given name and dataset.

    Args:
        name: The name of the project.
        dataset: The dataset of the project.

    Returns:
        The created project.

    Raises:
        ValueError: If parameters are invalid.
    """
    try:
        return Project(name, dataset)
    except AssertionError as e:
        raise ValueError(e)
