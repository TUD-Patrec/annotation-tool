import copy
import time
import logging
import numpy as np

from src.retrieval_backend.filter import FilterCriteria
from src.retrieval_backend.interval import Interval
from src.retrieval_backend.mode import RetrievalMode
from src.utility.decorators import accepts


class Query:
    def __init__(self, intervals: list) -> None:
        self._intervals = intervals
        self._indices = []  # for querying
        self._idx = -1
        self._marked_intervals = set()
        self._accepted_intervals = set()
        self._mode: RetrievalMode = RetrievalMode.DESCENDING
        self._filter_criterion: FilterCriteria = FilterCriteria()

        self.update_indices()

    def __len__(self):
        return len(self._indices)

    def get_next(self) -> Interval:
        assert self.has_next()
        next_unmarked_idx = self.get_next_unmarked_idx()
        self._idx = next_unmarked_idx

        index_to_interval = self._indices[next_unmarked_idx]
        interval = self._intervals[index_to_interval]
        return interval

    def has_next(self):
        return self.get_next_unmarked_idx() < len(self._indices)

    def get_next_unmarked_idx(self):
        idx = self._idx + 1
        while idx < len(self._indices):
            index_to_interval = self._indices[idx]
            if self._intervals[index_to_interval] not in self._marked_intervals:
                break
            idx += 1
        return idx

    def reset_marked_intervals(self):
        self._marked_intervals = copy.deepcopy(self._accepted_intervals)

    def reset_accepted_intervals(self):
        self._accepted_intervals = set()
        self._marked_intervals = set()
        self.update_indices()

    def apply_filter(self):
        indices = []
        for idx, interval in enumerate(self._intervals):
            if self._filter_criterion.matches(interval):
                indices.append(idx)
        self._indices = indices

    def reorder_indices(self):
        if self._mode == RetrievalMode.DESCENDING:
            ls = [
                (idx, self._intervals[idx].similarity) for idx in self._indices
            ]  # zip indices with similarities

            ls = sorted(ls, key=lambda x: x[1], reverse=True)  # Sorting by similarity
            self._indices = [x for x, _ in ls]

        if self._mode == RetrievalMode.DEFAULT:
            self._indices.sort()
        if self._mode == RetrievalMode.RANDOM:
            perm = np.random.permutation(np.array(self._indices))
            self._indices = list(perm)

    def update_indices(self):
        self.apply_filter()
        self.reorder_indices()
        self._idx = -1

    # modify _indices to only include those that match the filter criterium
    @accepts(object, FilterCriteria)
    def change_filter(self, criteria: FilterCriteria):
        start = time.time()
        if self._filter_criterion != criteria:
            self._filter_criterion = criteria
            self.update_indices()
        end = time.time()
        logging.info(f"CHANGE_FILTER TOOK {end - start}ms")

    # reorder the indices
    @accepts(object, RetrievalMode)
    def change_mode(self, mode: RetrievalMode):
        start = time.time()
        if mode != self._mode:
            self._mode = mode
            self.update_indices()
        end = time.time()
        print(f"CHANGE_MODE TOOK {end - start}ms")

    @accepts(object, Interval)
    def mark_interval(self, i: Interval):
        assert i not in self._marked_intervals
        self._marked_intervals.add(i)

    @accepts(object, Interval)
    def accept_interval(self, i: Interval):
        assert i not in self._accepted_intervals
        self._accepted_intervals.add(i)
        self._marked_intervals.add(i)

    @property
    def idx(self):
        return self._idx

    @property
    def filter_criterion(self):
        return self._filter_criterion
