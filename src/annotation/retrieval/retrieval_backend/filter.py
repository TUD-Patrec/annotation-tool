from dataclasses import dataclass, field

import numpy as np

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement


@dataclass(frozen=True)
class FilterCriterion:
    filter_array: np.ndarray = field(init=True, default=None)

    def matches(self, retrieval_element: RetrievalElement) -> bool:
        """
        Tests whether the given retrieval element matches the filter criterion.
        """
        if self.is_empty():
            # If the filter criterion is empty, it matches everything.
            return True

        comp_array: np.ndarray = retrieval_element.annotation.annotation_vector

        tmp = np.logical_and(comp_array, self.filter_array)
        res = np.array_equal(self.filter_array, tmp)

        return res

    def __eq__(self, other):
        if isinstance(other, FilterCriterion):
            if self.filter_array is None:
                return other.filter_array is None
            if other.filter_array is None:
                return False
            return np.array_equal(self.filter_array, other.filter_array)
        return False

    def __copy__(self):
        tmp = (
            np.copy(self.filter_array)
            if isinstance(self.filter_array, np.ndarray)
            else None
        )
        return FilterCriterion(tmp)

    def is_empty(self) -> bool:
        return self.filter_array is None or np.sum(self.filter_array) == 0
