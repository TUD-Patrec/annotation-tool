import numpy as np

from src.annotation.retrieval.retrieval_backend.filter import FilterCriteria
from src.annotation.retrieval.retrieval_backend.interval import Interval
from src.utility.decorators import accepts


class Query:
    def __init__(self, intervals: list) -> None:
        self._intervals = intervals
        self._indices = []  # for querying
        self._idx = -1
        self._sim_distr = None
        self._rejected_intervals = set()
        self._accepted_intervals = set()
        self._accepted_tuples = set()
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
            tmp = self._intervals[index_to_interval]
            accepted = (tmp.start, tmp.end) in self._accepted_tuples
            rejected = tmp in self._rejected_intervals
            if not (accepted or rejected):
                break
            idx += 1
        return idx

    def similarity_distribution(self, use_cached=True):
        if self._sim_distr is not None and use_cached:
            return self._sim_distr
        else:
            gen = [self._intervals[i].similarity for i in self._indices]
            self._sim_distr = np.array(gen, dtype=np.float32)
            return self._sim_distr

    def reset_rejected_intervals(self):
        self._rejected_intervals = set()

    def reset_accepted_intervals(self):
        self._accepted_tuples = set()
        self._accepted_intervals = set()
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
        if self._filter_criterion != criteria:
            self._filter_criterion = criteria
            self.update_indices()
            self.similarity_distribution(use_cached=False)

    @accepts(object, Interval)
    def accept_interval(self, i: Interval):
        if (i.start, i.end) not in self._accepted_tuples:
            self._accepted_tuples.add((i.start, i.end))
            self._accepted_intervals.add(i)

    @accepts(object, Interval)
    def reject_interval(self, i: Interval):
        self._rejected_intervals.add(i)

    @property
    def idx(self):
        return self._idx

    @property
    def filter_criterion(self):
        return self._filter_criterion
