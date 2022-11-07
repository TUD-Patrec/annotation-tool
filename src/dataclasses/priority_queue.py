from dataclasses import dataclass, field
import heapq
from typing import Any, Callable, List, Union


@dataclass(order=True)
class QueueItem:
    priority: Union[int, float] = field(compare=True)
    item: Any = field(compare=False)
    removed: bool = field(default=False, init=False, compare=False)


class PriorityQueue:
    def __init__(self) -> None:
        self._pq: List[QueueItem] = []
        self._lookup_dict = {}
        self._length = 0

    def __peek__(self) -> Union[Any, None]:
        """Return the next item in the queue without removing it."""
        while self._pq and self._pq[0].removed:
            heapq.heappop(self._pq)
            del self._lookup_dict[self._pq[0].item]
            self._length -= 1  # remove all removed items
        if self._pq:
            return self._pq[0].item
        else:
            return None

    def peek(self) -> Union[Any, None]:
        """Return the next item in the queue without removing it."""
        return self.__peek__()

    def __pop__(self) -> Union[Any, None]:
        """Return the next item in the queue and remove it."""
        while self._pq and self._pq[0].removed:
            heapq.heappop(self._pq)
            del self._lookup_dict[self._pq[0].item]
            self._length -= 1  # remove all removed items
        if self._pq:
            self._length -= 1  # remove the item from the queue
            del self._lookup_dict[self._pq[0].item]
            return heapq.heappop(self._pq).item
        else:
            return None

    def pop(self) -> Union[Any, None]:
        """Return the next item in the queue and remove it."""
        return self.__pop__()

    def __push__(
        self, item: Any, key: Union[Callable, Union[int, float]] = None
    ) -> None:
        """Push an item into the queue.

        Args:
            item: The item to be pushed into the queue, must be hashable.
            key: The key to be used for sorting the queue. If None, the item itself is used.
        """
        if key is None:

            def key(x):
                return x  # default key is the item itself

        if isinstance(key, float):
            priority = key  # if key is a float, use it as priority
        else:
            priority = key(item)  # get the priority of the item
        queue_item = QueueItem(priority, item)
        heapq.heappush(self._pq, queue_item)
        self._lookup_dict[item] = queue_item
        self._length += 1

    def push(self, item: Any, key: Union[Callable, Union[int, float]] = None) -> None:
        """Push an item into the queue.

        Args:
            item: The item to be pushed into the queue, must be hashable.
            key: The key to be used for sorting the queue. If None, the item itself is used.
        """
        self.__push__(item, key)

    def __remove__(self, item: Any) -> None:
        """Remove an item from the queue."""
        if item in self._lookup_dict:
            self._lookup_dict[item].removed = True
            self._length -= 1

    def remove(self, item: Any) -> None:
        """Remove an item from the queue."""
        self.__remove__(item)

    def __len__(self) -> int:
        return self._length

    def to_list(self) -> List[Any]:
        non_removed = [queue_item for queue_item in self._pq if not queue_item.removed]
        ls = sorted(
            non_removed, key=lambda x: x.priority, reverse=True
        )  # sort by priority in descending order
        return [queue_item.item for queue_item in ls]

    def __iter__(self):
        return iter(self.to_list())

    def clear(self):
        self._pq = []
        self._lookup_dict = {}
        self._length = 0
