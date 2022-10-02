import time
import logging

import numpy as np

from src.retrieval_backend.filter import FilterCriteria
from src.retrieval_backend.interval import Interval
from src.utility.decorators import accepts


class Query:
    def __init__(self, intervals: list) -> None:
        self._intervals = intervals
        self._indices = []  # for querying
        self._idx = -1
        self._marked_intervals = set()
        self._accepted_intervals = set()
        self._filter_criterion: FilterCriteria = FilterCriteria()

        self.update_indices()

    def __len__(self):
        return len(self._indices)

    def __iter__(self):
        self._idx = -1
        return self

    def __next__(self):
        if self.has_next():
            self._idx = self.get_next_unmarked_idx()

            interval_idx = self._indices[self.idx]
            interval = self._intervals[interval_idx]
            return interval
        else:
            raise StopIteration

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

    def remaining_similarities(self):
        similarities = []
        for idx in self._indices[self._idx :]:
            interval = self._intervals[idx]
            if interval not in self._accepted_intervals:
                similarities.append(interval.similarity)
        return np.array(similarities, dtype=np.float32)

    def similarity_distribution(self):
        if hasattr(self, "_sim"):
            return self._sim
        else:
            gen = [self._intervals[i].similarity for i in self._indices]
            self._sim = np.array(gen)
            return self._sim

    def reset_marked_intervals(self):
        self._marked_intervals = {interval for interval in self._accepted_intervals}

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

    def order_indices(self):
        ls = [
            (idx, self._intervals[idx].similarity) for idx in self._indices
        ]  # zip indices with similarities

        ls = sorted(ls, key=lambda x: x[1], reverse=True)  # Sorting by similarity
        self._indices = [x for x, _ in ls]

    def update_indices(self):
        self.apply_filter()
        self.order_indices()
        self._idx = -1

    # modify _indices to only include those that match the filter criterium
    @accepts(object, FilterCriteria)
    def change_filter(self, criteria: FilterCriteria):
        start = time.perf_counter()
        if self._filter_criterion != criteria:
            self._filter_criterion = criteria
            self.update_indices()
        end = time.perf_counter()
        logging.debug(f"CHANGE_FILTER TOOK {end - start}ms")

    @accepts(object, Interval)
    def mark_interval(self, i: Interval):
        self._marked_intervals.add(i)

    @accepts(object, Interval)
    def accept_interval(self, i: Interval):
        self._accepted_intervals.add(i)
        self._marked_intervals.add(i)

    @property
    def idx(self):
        return self._idx

    @property
    def filter_criterion(self):
        return self._filter_criterion
