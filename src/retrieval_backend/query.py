import time

import numpy as np

from src.retrieval_backend.filter import FilterCriteria
from src.retrieval_backend.interval import Interval
from src.retrieval_backend.mode import RetrievalMode


class Query:
    def __init__(self, intervals: list) -> None:
        self._intervals = intervals
        self._indices = []  # for querying
        self._idx = -1
        self._marked_intervals = set()  # for marking intervals as DONE
        self._mode: RetrievalMode = RetrievalMode.DESCENDING
        self._filter_criteria: FilterCriteria = None

        self.debug_count = 0

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

    def apply_filter(self):
        if self._filter_criteria:
            indices = []
            for idx in range(len(self._intervals)):
                if self._filter_criteria.matches(self._intervals[idx]):
                    indices.append(idx)
        else:
            indices = list(range(len(self._intervals)))
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
        self._idx = -1

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
        assert i not in self._marked_intervals
        self.debug_count += 1
        # print(self.debug_count)
        self._marked_intervals.add(i)

    @property
    def idx(self):
        return self._idx
