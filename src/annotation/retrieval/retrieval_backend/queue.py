from dataclasses import dataclass, field
import logging
from typing import Dict, List, Union

from sortedcontainers import SortedList

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.dataclasses.priority_queue import PriorityQueue


@dataclass(order=True)
class RetrievalQueueWrapper:
    similarity: Union[int, float] = field(compare=True)
    interval: int = field(compare=True)
    item: PriorityQueue = field(compare=False)


class RetrievalQueue:
    def __init__(self):
        super().__init__()
        self._q_wrappers: SortedList[RetrievalQueueWrapper] = SortedList()
        self._interval_to_q_wrapper: Dict[int, RetrievalQueueWrapper] = {}

    def __len__(self) -> int:
        """Return the number of subqueues."""
        return len(self._q_wrappers)

    def push(self, element: RetrievalElement) -> None:
        """Add an element to the queue."""

        i = element.interval_index
        if i not in self._interval_to_q_wrapper:
            # create a new subqueue
            new_queue = PriorityQueue()
            queue_wrapper = RetrievalQueueWrapper(element.similarity, i, new_queue)
            self._interval_to_q_wrapper[
                i
            ] = queue_wrapper  # add to interval to queue mapping
            self._q_wrappers.add(queue_wrapper)  # add to sorted list of queues
            print("Added new queue for interval %d" % i)
            print(queue_wrapper)
            print()
        else:
            queue_wrapper = self._interval_to_q_wrapper[i]

        queue = queue_wrapper.item  # get the queue
        size_before = len(queue)
        queue.push(element, key=1 - element.similarity)  # add the element to the queue
        size_after = len(queue)
        assert (
            size_after == size_before + 1
        ), "[Sub]-Queue size did not increase by 1. {} != {}".format(
            size_after, size_before + 1
        )

        s1 = len(queue)
        if element.similarity > queue_wrapper.similarity:
            # update the similarity of the queue item if necessary
            self._q_wrappers.remove(queue_wrapper)  # => O(log n)
            queue_wrapper.similarity = element.similarity
            self._q_wrappers.add(queue_wrapper)  # => O(log n)
        s2 = len(queue)
        assert s1 == s2, "Queue size changed. {} != {}".format(s1, s2)

    def remove(self, element: RetrievalElement) -> None:
        """Remove an element from the queue."""
        i = element.interval_index
        if i not in self._interval_to_q_wrapper:
            return

        queue_wrapper = self._interval_to_q_wrapper[i]
        self._q_wrappers.remove(queue_wrapper)

        queue = queue_wrapper.item
        old_size = len(queue)
        queue.remove(element)
        new_size = len(queue)
        assert (
            old_size == new_size + 1
        ), "Queue size did not decrease by 1. {} != {}".format(old_size, new_size + 1)

        if len(queue) > 0:
            queue_wrapper.similarity = queue.peek().similarity
            self._q_wrappers.add(queue_wrapper)
        else:
            del self._interval_to_q_wrapper[i]

    def pop(self) -> Union[RetrievalElement, None]:
        """Return the next element in the queue and remove it."""
        if len(self._q_wrappers) == 0:
            return None

        queue_wrapper = self._q_wrappers.pop()
        queue = queue_wrapper.item
        old_size = len(queue)
        element = queue.pop()
        new_size = len(queue)

        assert (
            old_size == new_size + 1
        ), "Queue size did not decrease by 1. {} != {}".format(old_size, new_size + 1)
        assert element is not None, "Element is None."

        if len(queue) > 0:
            queue_wrapper.similarity = queue.peek().similarity
            self._q_wrappers.add(queue_wrapper)
        else:
            del self._interval_to_q_wrapper[element.interval_index]

        return element

    def peek(self) -> Union[RetrievalElement, None]:
        """Return the next element in the queue without removing it."""
        if len(self._q_wrappers) == 0:
            return None

        queue_wrapper = self._q_wrappers[0]
        queue = queue_wrapper.item

        old_size = len(queue)
        element = queue.peek()
        new_size = len(queue)
        assert old_size == new_size, "Queue size changed. {} != {}".format(
            old_size, new_size
        )

        assert element is not None

        return element

    def total_length(self) -> int:
        """Return the total number of elements in the queue."""
        return sum([len(queue.item) for queue in self._q_wrappers])

    def __contains__(self, element: RetrievalElement) -> bool:
        """Check if the queue contains an element."""
        i = element.interval_index
        if i not in self._interval_to_q_wrapper:
            return False

        queue_wrapper = self._interval_to_q_wrapper[i]
        queue = queue_wrapper.item
        return element in queue

    def __iter__(self):
        """Return an iterator over the queue."""
        return iter(self.to_list())

    def to_list(self) -> List[RetrievalElement]:
        """Return the queue as a list."""
        queues = [queue_wrapper.item for queue_wrapper in self._q_wrappers]
        # grab all elements
        elements = [element for queue in queues for element in queue]
        elements.sort(key=lambda x: x.similarity, reverse=True)
        return elements

    def remove_interval(self, i: int) -> None:
        """Remove all elements from the queue that belong to the given interval."""
        if i not in self._interval_to_q_wrapper:
            logging.warning("Interval %d not in queue.", i)
            return

        old_size = self.total_length()

        queue_wrapper = self._interval_to_q_wrapper[i]

        s1 = len(self._q_wrappers)
        self._q_wrappers.remove(queue_wrapper)
        s2 = len(self._q_wrappers)
        assert s1 == s2 + 1, "_q_wrappers size did not decrease by 1. %d != %d" % (
            s1,
            s2,
        )

        queue = queue_wrapper.item
        new_size = self.total_length()
        assert old_size == new_size + len(
            queue
        ), "Queue size did not decrease by the size of the removed queue. {} != {} + {}".format(
            old_size, new_size, len(queue)
        )

        queue.clear()  # remove all elements from the queue
        del self._interval_to_q_wrapper[i]

    def clear(self):
        self._q_wrappers.clear()
        self._interval_to_q_wrapper.clear()