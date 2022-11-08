import logging
import time
from typing import List, Set, Union

import numpy as np

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.annotation.retrieval.retrieval_backend.filter import FilterCriterion
from src.annotation.retrieval.retrieval_backend.queue import RetrievalQueue


class Query:
    def __init__(self, retrieval_list: List[RetrievalElement]) -> None:
        self._retrieval_list: List[RetrievalElement] = sorted(
            retrieval_list, key=lambda x: (x.distance, x.i, x.j)
        )  # list of all retrieval elements, must never be changed!
        self.accepted_elements: Set[RetrievalElement] = set()  # accepted elements
        self.rejected_elements: Set[RetrievalElement] = set()  # rejected elements
        self._filter_criterion: FilterCriterion = FilterCriterion()  # filter criterion

        # gaining some efficiency by caching and smarter datastructures
        self._retrieval_queue: RetrievalQueue = None  # queue of open elements
        self.__build_queue__()  # build queue

    def __len__(self) -> int:
        """Returns the number of elements in the query."""
        # number of processed intervals = number of accepted elements
        n_processed_intervals = len(self.accepted_elements)
        n_open_intervals = len(self.open_intervals)
        return n_processed_intervals + n_open_intervals

    def __next__(self) -> Union[RetrievalElement, None]:
        """Returns the next RetrievalElement."""
        if self.open_elements:
            self.__check_consistency__()  # check integrity of query before processing next element
            return self.open_elements.pop()
        else:
            return None

    def __build_queue__(self) -> None:
        """Builds the queue from scratch."""
        start = time.perf_counter()
        open_elements = self.__compute_open_elements()  # compute open elements
        self._retrieval_queue = RetrievalQueue()  # create new queue

        for elem in open_elements:
            old_size = self._retrieval_queue.total_length()
            self._retrieval_queue.push(elem)
            new_size = self._retrieval_queue.total_length()
            assert new_size - old_size == 1, "Queue size did not increase by 1."

        assert (
            len(open_elements) == self._retrieval_queue.total_length()
        ), "Queue size does not match number of open elements."

        end = time.perf_counter()
        logging.info(f"Computing open elements took {end - start} seconds.")

    def __check_consistency__(self):
        """Checks the consistency of the query."""

        start = time.perf_counter()

        fst = self.open_elements.pop()
        self.open_elements.push(fst)
        assert (
            fst == self.open_elements.peek()
        ), "Queue does not return correct element."

        xs = self.__compute_open_elements()

        assert (
            len(xs) == self._retrieval_queue.total_length()
        ), "Queue size does not match number of open elements. {} vs {}".format(
            len(xs), self._retrieval_queue.total_length()
        )

        assert (
            xs[0] == self.open_elements.peek()
        ), "First element of open elements does not match first element of retrieval list."

        ys = list(self._retrieval_queue)

        assert len(xs) == len(
            ys
        ), "Number of open elements does not match number of elements in queue."

        for idx, (x, y) in enumerate(zip(xs, ys)):
            assert (
                x == y
            ), f"{idx}: Element {x} of open elements does not match element {y} of queue."

        end = time.perf_counter()
        logging.info(f"check_consistency took {end - start} seconds.")

    def __is_processed__(self, elem: RetrievalElement) -> bool:
        """Checks if the given element has already been accepted or rejected by the user."""
        return elem in self.accepted_elements or elem in self.rejected_elements

    def __is_open_element__(self, element: RetrievalElement) -> bool:
        """
        Checks if the given element is open.
        An element is open if:
            1) it is not processed yet
            2) it matches the filter criterion
            3) its interval is not accepted yet (i.e. there is no accepted element in the interval).
        """
        if self.__is_processed__(element):
            return False
        if not self._filter_criterion.matches(element):
            return False
        if element.interval_index in self.accepted_intervals:
            return False
        return True

    def __compute_open_elements(self) -> List[RetrievalElement]:
        """Computes the open elements that match the filter criterion."""
        return [x for x in self._retrieval_list if self.__is_open_element__(x)]

    @property
    def open_elements(self) -> RetrievalQueue:
        """Returns the open elements that match the filter criterion.
        Keeps the order of the retrieval list."""
        assert self._retrieval_queue is not None, "Queue is not initialized."
        return self._retrieval_queue

    @property
    def open_intervals(self) -> List[int]:
        """Returns the open intervals.
        same as np.unique([elem.interval_index for elem in self.open_elements]) but faster."""
        assert self._retrieval_queue is not None, "Queue is not initialized."
        return self._retrieval_queue.intervals

    @property
    def processed_elements(self) -> Set[RetrievalElement]:
        """
        Returns the set of processed elements.
        Should be avoided, since it is not efficient.
        """
        return self.accepted_elements.union(self.rejected_elements)

    @property
    def accepted_intervals(self) -> Set[int]:
        """Returns the set of accepted intervals."""
        return {elem.interval_index for elem in self.accepted_elements}

    @property
    def current_index(self) -> int:
        """Returns the current index of the query.
        The current index is the index of the last accepted element."""
        return len(self.accepted_elements)

    @property
    def filter_criterion(self) -> FilterCriterion:
        """Returns the filter criterion."""
        return self._filter_criterion

    @property
    def similarity_distribution(self) -> np.ndarray:
        """Returns the distance distribution of the query."""

        start = time.perf_counter()

        accepted_similarities = np.array(
            [elem._similarity for elem in self.accepted_elements]
        )

        open_similarities = [
            self._retrieval_queue.peek_into_interval(i)._similarity
            for i in self.open_intervals
        ]

        # get similarity distribution
        similarity_distribution = np.concatenate(
            (accepted_similarities, open_similarities)
        )

        end = time.perf_counter()
        logging.info(
            f"Computing the similarity_distribution took {(end - start):.3f} seconds in total."
        )

        return similarity_distribution

    def set_filter(self, new_filter: FilterCriterion) -> None:
        """Sets the filter set."""
        if self._filter_criterion != new_filter:
            self._filter_criterion = new_filter
            self.__build_queue__()  # build queue from scratch

    def accept(self, element: RetrievalElement) -> None:
        """Accepts the element."""
        assert not self.__is_processed__(element), "Element is already processed."
        assert (
            element.interval_index not in self.accepted_intervals
        ), "Interval is already accepted."
        self.accepted_elements.add(element)
        if self.open_elements:
            self.open_elements.remove_interval(
                element.interval_index
            )  # remove interval from queue

    def reject(self, element: RetrievalElement) -> None:
        """Rejects the element."""
        assert not self.__is_processed__(element), "Element is already processed."
        self.rejected_elements.add(element)

    def reset_filter(self) -> None:
        """Resets the filter."""
        self.set_filter(FilterCriterion())

    def reset_rejected(self) -> None:
        """Resets the rejected elements."""
        self.rejected_elements = set()
        self.__build_queue__()  # build queue from scratch

    def reset(self) -> None:
        """Resets the query."""
        self.accepted_elements = set()
        self.rejected_elements = set()
        self._filter_criterion = FilterCriterion()
        self.__build_queue__()  # build queue from scratch
