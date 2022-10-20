from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class FilterCriteria:
    filter_array: np.ndarray = field(init=True, default=None)

    # test whether a given interval matches the criterion
    def matches(self, i):
        if self.is_empty():
            return True
        comp_array = i.annotation.annotation_vector

        tmp = np.logical_and(comp_array, self.filter_array)
        res = np.array_equal(self.filter_array, tmp)

        return res

    def __eq__(self, other):
        if isinstance(other, FilterCriteria):
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
        return FilterCriteria(tmp)

    def is_empty(self):
        return self.filter_array is None or np.sum(self.filter_array) == 0
