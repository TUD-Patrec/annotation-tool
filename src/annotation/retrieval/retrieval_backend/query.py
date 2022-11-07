from typing import Iterable, List, Set, Union

import numpy as np

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.annotation.retrieval.retrieval_backend.filter import FilterCriterion
from src.annotation.retrieval.retrieval_backend.queue import RetrievalQueue


class Query:
    def __init__(self, retrieval_list: List[RetrievalElement]) -> None:
        self._retrieval_list: List[RetrievalElement] = sorted(
            retrieval_list, key=lambda x: x.similarity, reverse=True
        )  # list of all retrieval elements, must never be changed!
        self.accepted_elements: Set[RetrievalElement] = set()  # accepted elements
        self.rejected_elements: Set[RetrievalElement] = set()  # rejected elements
        self._filter_criterion: FilterCriterion = FilterCriterion()  # filter criterion

        # gaining some efficiency by caching and smarter datastructures
        self._retrieval_queue: RetrievalQueue = None

    @property
    def similarity_distribution(self) -> np.ndarray:
        """Returns the similarity distribution of the query."""

        accepted_similarities = np.array(
            [elem.similarity for elem in self.accepted_elements]
        )

        # get similarities of open intervals
        open_intervals_with_similarities = np.array(
            [[elem.interval_index, elem.similarity] for elem in self.open_elements]
        )

        # group similarities by interval index
        grouped_similarities = [
            open_intervals_with_similarities[
                open_intervals_with_similarities[:, 0] == i
            ][:, 1]
            for i in self.open_intervals
        ]

        # compute max similarity for each interval
        max_similarities = np.array(
            [np.max(similarities) for similarities in grouped_similarities]
        )

        # get similarity distribution
        similarity_distribution = np.concatenate(
            (accepted_similarities, max_similarities)
        )
        similarity_distribution = np.sort(similarity_distribution)

        return similarity_distribution

    @property
    def open_elements(self) -> Iterable[RetrievalElement]:
        """Returns the open elements that match the filter criterion.
        Keeps the order of the retrieval list."""
        if self._retrieval_queue is None:

            def _check(x):
                return (
                    x.interval_index not in self.accepted_intervals
                    and self._filter_criterion.matches(x)
                    and x not in self.rejected_elements
                )

            open_elements = [x for x in self._retrieval_list if _check(x)]

            self._retrieval_queue = RetrievalQueue()

            intvls = set()

            for elem in open_elements:
                intvls.add(elem.interval_index)
                old_size = self._retrieval_queue.total_length()
                self._retrieval_queue.push(elem)
                new_size = self._retrieval_queue.total_length()
                assert new_size - old_size == 1, "Queue size did not increase by 1."

            print(f"Open intervals: {intvls}")
            print(f"len(_retrieval_queue): {len(self._retrieval_queue)}")
            print(
                f"total_length(_retrieval_queue): {self._retrieval_queue.total_length()}"
            )

            assert (
                len(open_elements) == self._retrieval_queue.total_length()
            ), "Queue size does not match number of open elements."

        return self._retrieval_queue

    @property
    def processed_elements(self) -> Set[RetrievalElement]:
        """Returns the set of processed elements."""
        return self.accepted_elements | self.rejected_elements

    @property
    def open_intervals(self) -> List[int]:
        """Returns the open intervals."""
        return sorted(np.unique([elem.interval_index for elem in self.open_elements]))

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

    def __len__(self) -> int:
        """Returns the number of elements in the query."""
        # number of processed intervals = number of accepted elements
        n_processed_intervals = len(self.accepted_elements)
        n_open_intervals = len(self.open_intervals)
        return n_processed_intervals + n_open_intervals

    def __next__(self) -> Union[RetrievalElement, None]:
        """Returns the next RetrievalElement."""
        if self.open_elements:
            return self.open_elements.pop()
        else:
            return None

    def set_filter(self, new_filter: FilterCriterion) -> None:
        """Sets the filter set."""
        self._filter_criterion = new_filter
        self._retrieval_queue = None

    def accept(self, element: RetrievalElement) -> None:
        """Accepts the element."""
        assert element not in self.processed_elements  # element must not be processed
        assert element.interval_index not in self.accepted_intervals
        self.accepted_elements.add(element)
        if self.open_elements:
            self.open_elements.remove_interval(
                element.interval_index
            )  # remove interval from queue

    def reject(self, element: RetrievalElement) -> None:
        """Rejects the element."""
        assert element not in self.processed_elements  # element must not be processed
        self.rejected_elements.add(element)

    def reset(self) -> None:
        """Resets the query."""
        self.accepted_elements = set()
        self.rejected_elements = set()
        self.reset_filter()

    def reset_filter(self) -> None:
        """Resets the filter."""
        self.set_filter(FilterCriterion())

    def reset_rejected(self) -> None:
        """Resets the rejected elements."""
        self.rejected_elements = set()
        self._retrieval_queue = None
