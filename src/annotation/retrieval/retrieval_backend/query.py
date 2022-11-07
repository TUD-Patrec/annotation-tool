from typing import Dict, List, Set, Tuple, Union

import numpy as np
from sortedcontainers import SortedList

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.annotation.retrieval.retrieval_backend.filter import FilterCriterion
from src.dataclasses.priority_queue import PriorityQueue, QueueItem


class RetrievalQueue:
    def __init__(self):
        super().__init__()
        self._subqueues: SortedList[QueueItem] = SortedList()
        self._interval_to_queue: Dict[int, QueueItem] = {}

    def __len__(self) -> int:
        """Return the number of subqueues in the queue."""
        return len(self._subqueues)

    def add_element(self, element: RetrievalElement) -> None:
        """Add an element to the queue."""
        i = element.interval_index
        if i not in self._interval_to_queue:
            # create a new subqueue
            queue_item = QueueItem(element.similarity, PriorityQueue())
        else:
            queue_item = self._interval_to_queue[i]
            self._subqueues.remove(queue_item)

        queue = queue_item.item
        queue.push(element)

        queue_item.priority = queue.peek().similarity

        self._subqueues.add(queue_item)

    def remove_element(self, element: RetrievalElement) -> None:
        """Remove an element from the queue."""
        i = element.interval_index
        if i not in self._interval_to_queue:
            return

        queue_item = self._interval_to_queue[i]
        self._subqueues.remove(queue_item)

        queue = queue_item.item
        queue.remove(element)

        if len(queue) > 0:
            queue_item.priority = queue.peek().similarity
            self._subqueues.add(queue_item)
        else:
            del self._interval_to_queue[i]

    def pop(self) -> Union[RetrievalElement, None]:
        """Return the next element in the queue and remove it."""
        if len(self._subqueues) == 0:
            return None

        queue_item = self._subqueues.pop(0)
        queue = queue_item.item
        element = queue.pop()

        if len(queue) > 0:
            queue_item.priority = queue.peek().similarity
            self._subqueues.add(queue_item)
        else:
            del self._interval_to_queue[element.interval_index]

        return element

    def peek(self) -> Union[RetrievalElement, None]:
        """Return the next element in the queue without removing it."""
        if len(self._subqueues) == 0:
            return None

        queue_item = self._subqueues[0]
        queue = queue_item.item
        element = queue.peek()

        return element

    def total_length(self) -> int:
        """Return the total number of elements in the queue."""
        return sum([len(queue.item) for queue in self._subqueues])

    def __contains__(self, element: RetrievalElement) -> bool:
        """Check if the queue contains an element."""
        i = element.interval_index
        if i not in self._interval_to_queue:
            return False

        queue_item = self._interval_to_queue[i]
        queue = queue_item.item
        return element in queue

    def to_list(self) -> List[RetrievalElement]:
        """Return the queue as a list."""
        ls = [element for queue in self._subqueues for element in queue.item.to_list()]
        return ls


class Query:
    def __init__(self, retrieval_list: List[RetrievalElement]) -> None:
        self._retrieval_list: List[RetrievalElement] = sorted(
            retrieval_list, key=lambda x: x.similarity, reverse=True
        )  # list of all retrieval elements, must never be changed!
        self.accepted_elements: Set[RetrievalElement] = set()  # accepted elements
        self.rejected_elements: Set[RetrievalElement] = set()  # rejected elements
        self._filter_criterion: FilterCriterion = FilterCriterion()  # filter criterion

        # gaining some efficiency by caching the results
        self._open_elements: RetrievalQueue = None

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
    def open_elements(self) -> List[RetrievalElement]:
        """Returns the open elements that match the filter criterion.
        Keeps the order of the retrieval list."""
        if self._open_elements is None:

            def _check(x):
                return (
                    x.interval_index not in self.accepted_intervals
                    and self._filter_criterion.matches(x)
                    and x not in self.rejected_elements
                )

            open_elements = [x for x in self._retrieval_list if _check(x)]

            self._open_elements = RetrievalQueue()

            for elem in open_elements:
                self._open_elements.add_element(elem)

        return self._open_elements.to_list()

    @property
    def processed_elements(self) -> Set[RetrievalElement]:
        """Returns the set of processed elements."""
        return self.accepted_elements | self.rejected_elements

    @property
    def open_intervals(self) -> List[int]:
        """Returns the open intervals."""
        return np.unique([elem.interval_index for elem in self.open_elements])

    @property
    def accepted_intervals(self) -> Set[int]:
        """Returns the set of accepted intervals."""
        return {elem.interval_index for elem in self.accepted_elements}

    @property
    def current_index(self) -> int:
        """Returns the current index of the iterator."""
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

    def __next__(self) -> Union[Tuple, None]:
        """Returns the next retrieval element."""
        if self.open_elements:
            return self.open_elements.pop(0)  # pop leftmost element
        else:
            return None

    def set_filter(self, new_filter: FilterCriterion) -> None:
        """Sets the filter set."""
        self._filter_criterion = new_filter
        self._open_elements = None

    def accept(self, element: RetrievalElement) -> None:
        """Accepts the element."""
        assert element not in self.processed_elements  # element must not be processed
        assert element.interval_index not in self.accepted_intervals
        self.accepted_elements.add(element)

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
        self._open_elements = None
