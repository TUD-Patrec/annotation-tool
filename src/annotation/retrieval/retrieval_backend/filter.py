from dataclasses import dataclass, field

import numpy as np

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement


@dataclass(frozen=True)
class FilterCriterion:
    filter_array: np.ndarray = field(init=True, default=None)

    def matches(self, retrieval_element: RetrievalElement) -> bool:
        """
        Tests whether the given retrieval element matches the filter criterion.

        Args:
            retrieval_element: The retrieval element to test.

        Returns:
            True if the retrieval element matches the filter criterion, False otherwise.
        """
        if self.is_empty():
            # If the filter criterion is empty, it matches everything.
            return True

        comp_array: np.ndarray = retrieval_element.annotation.annotation_vector

        tmp = np.logical_and(comp_array, self.filter_array)
        res = np.array_equal(self.filter_array, tmp)

        return res

    def __eq__(self, other) -> bool:
        """
        Tests whether the given filter criterion is equal to this one.

        Args:
            other: The other filter criterion.
        """
        if isinstance(other, FilterCriterion):
            if self.is_empty():
                return other.is_empty()
            else:
                return np.array_equal(self.filter_array, other.filter_array)
        return False

    def __copy__(self) -> "FilterCriterion":
        """
        Returns a copy of this filter criterion.
        """
        tmp = (
            np.copy(self.filter_array)
            if isinstance(self.filter_array, np.ndarray)
            else None
        )
        return FilterCriterion(tmp)

    def is_empty(self) -> bool:
        """
        Tests whether the filter criterion is empty.

        Returns:
            True if the filter criterion is empty, False otherwise.
        """
        return self.filter_array is None or np.sum(self.filter_array) == 0
