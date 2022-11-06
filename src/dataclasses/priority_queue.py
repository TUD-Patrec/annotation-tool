from dataclasses import dataclass, field
import heapq
from typing import Any, Union


@dataclass(order=True)
class PrioritizedItem:
    priority: float
    item: Any = field(compare=False)


class PriorityQueue:
    def __init__(self) -> None:
        self.data = []

    def __peek__(self) -> Union[PrioritizedItem, None]:
        return self.data[0] if self.data else None

    def peek(self) -> Union[PrioritizedItem, None]:
        return self.__peek__()

    def __pop__(self) -> Union[PrioritizedItem, None]:
        return heapq.heappop(self.data) if self.data else None

    def pop(self) -> Union[PrioritizedItem, None]:
        return self.__pop__()

    def __push__(self, item: PrioritizedItem) -> None:
        heapq.heappush(self.data, item)

    def push(self, item: PrioritizedItem) -> None:
        self.__push__(item)

    def __len__(self):
        return len(self.data)
