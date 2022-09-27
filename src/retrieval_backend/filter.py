from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class FilterCriteria:
    filter_array: np.ndarray

    # test whether a given interval matches the criterion
    def matches(self, i):
        comp_array = i.predicted_classification
        tmp = np.logical_and(comp_array, self.filter_array)
        res = np.array_equal(self.filter_array, tmp)
        return res

    def __eq__(self, other):
        if isinstance(other, FilterCriteria):
            return np.array_equal(self.filter_array, other.filter_array)
        return False
