from dataclasses import dataclass, field
import logging
import time
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
from enum import Enum
import numpy as np
from scipy import spatial
from copy import deepcopy

# from .data_classes.sample import Sample


class RetrievalMode(Enum):
    DEFAULT = 0
    DESCENDING = 1
    RANDOM = 2


@dataclass(frozen=True)
class Interval:
    start: int
    end: int
    predicted_classification: np.ndarray = field(hash=False)
    similarity: float


@dataclass(frozen=True)
class FilterCriteria:
    filter_array: np.ndarray

    # test whether a given interval matches the criterion
    # TODO
    def matches(self, i):
        comp_array = i.predicted_classification
        tmp = np.logical_and(comp_array, self.filter_array)
        res = np.array_equal(self.filter_array, tmp)
        return res

    def __eq__(self, other):
        if isinstance(other, FilterCriteria):
            return np.array_equal(self.filter_array, other.filter_array)
        return False


class Query:
    def __init__(self, intervals: list) -> None:
        self._intervals = intervals
        self._indices = []  # for querying
        self._idx = 0
        self._marked_intervals = set()  # for marking intervals as DONE
        self._mode: RetrievalMode = RetrievalMode.DESCENDING
        self._filter_criteria: FilterCriteria = None

        self.update_indices()

    def __len__(self):
        return len(self._indices)

    def get_next(self) -> Interval:
        assert self.has_next()
        idx = self._indices[self._idx]
        self._idx += 1
        return self._intervals[idx]

    def has_next(self):
        assert 0 <= self._idx <= len(self._indices)
        return self._idx < len(self._indices)

    def apply_filter(self):
        indices = []
        for idx in range(len(self._intervals)):
            if self._intervals[idx] in self._marked_intervals:
                continue
            if self._filter_criteria is None or self._filter_criteria.matches(
                self._intervals[idx]
            ):
                indices.append(idx)

        self._indices = indices

    def reorder_indices(self):
        if self._mode == RetrievalMode.DESCENDING:
            print("CHANGING TO DESCENDING")
            ls = [
                (idx, self._intervals[idx].similarity) for idx in self._indices
            ]  # zip indices with similarities

            ls = sorted(ls, key=lambda x: x[1], reverse=True)  # Sorting by similarity
            self._indices = [x for x, _ in ls]

        if self._mode == RetrievalMode.DEFAULT:
            print("CHANGING TO DEFAULT")
            self._indices.sort()
        if self._mode == RetrievalMode.RANDOM:
            print("CHANGING TO RANDOM")
            perm = np.random.permutation(np.array(self._indices))
            self._indices = list(perm)

    def update_indices(self):
        self.apply_filter()
        self.reorder_indices()
        self._idx = 0

    # modify _indices to only include those that match the filter criterium
    def change_filter(self, criteria: FilterCriteria):
        start = time.time()
        reason_1 = self._filter_criteria is None and criteria is not None
        reason_2 = self._filter_criteria is not None and criteria is None
        reason_3 = self._filter_criteria != criteria
        if reason_1 or reason_2 or reason_3:
            self._filter_criteria = criteria
            self.update_indices()
        end = time.time()
        print(f"CHANGE_FILTER TOOK {end - start}ms")

    # reorder the indices
    def change_mode(self, mode: RetrievalMode):
        start = time.time()
        if mode != self._mode:
            self._mode = mode
            self.update_indices()
        end = time.time()
        print(f"CHANGE_MODE TOOK {end - start}ms")

    def mark_as_done(self, i: Interval):
        self._marked_intervals.add(i)

    @property
    def idx(self):
        return self._idx


class QRetrievalWidget(qtw.QWidget):
    # new_sample = qtc.pyqtSignal(Sample)
    start_loop = qtc.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(QRetrievalWidget, self).__init__(*args, **kwargs)
        # Controll attributes
        self.query: Query = None
        self.current_interval = None
        self._overlap: float = 0
        self._window_size: int = None
        self.init_layout()

    def init_layout(self):
        pass

    def load_annotation(self, a):
        pass

    # initialize the intervals from the given annotation
    def init_intervals(self):
        pass

    def init_query(self):
        pass

    # Display the current interval to the user: Show him the Interval boundaries and the predicted annotation, start the loop,
    def display_interval(self):
        pass

    # ask user for manual annotation -> used as a last option kind of thing or also whenever the user feels like it is needed
    def manually_annotate_interval(self):
        pass

    # same as manually_annotate_interval except that the annotation is preloaded with the suggested annotation
    def modify_interval_prediction(self):
        pass

    # accept the prediction from the network -> mark the interval as done
    def accept_interval(self):
        pass

    # dont accept the prediction
    def decline_interval(self):
        pass

    # Main function
    def retieval(self):
        pass

    @qtc.pyqtSlot()
    def settings_changed(self):
        pass

    @qtc.pyqtSlot(RetrievalMode)
    def change_mode(self, mode):
        pass

    @qtc.pyqtSlot(FilterCriteria)
    def change_filter(self, f):
        pass


if __name__ == "__main__":
    intervals = []
    start = 0

    array_length = 100
    N_intervals = 1000
    step_size = 100

    expected = np.random.randint(2, size=array_length)
    cos_sim = lambda x, y: 1 - spatial.distance.cosine(x, y)

    for _ in range(N_intervals):
        end = start + step_size - 1
        x = np.random.randint(2, size=array_length)
        interval = Interval(start, end, x, cos_sim(expected, x))
        start = end + 1
        intervals.append(interval)

    query = Query(intervals)

    filter_array = np.zeros(array_length)
    filter_array[0] = 1
    filter_array[1] = 1
    filter_array[2] = 1

    filter = FilterCriteria(filter_array)

    print(f"Before filter: {len(query) = }")
    query.change_filter(filter)
    print(f"After filter: {len(query) = }")

    query.change_mode(RetrievalMode.DEFAULT)
    # for _ in range(10):
    #    print(query.idx, query._indices[query.idx], query.get_next())
    query.change_mode(RetrievalMode.DESCENDING)
    for _ in range(10):
        print(query.idx, query._indices[query.idx], query.get_next())
    query.change_mode(RetrievalMode.RANDOM)
    # for _ in range(10):
    #    print(query.idx, query._indices[query.idx], query.get_next())
