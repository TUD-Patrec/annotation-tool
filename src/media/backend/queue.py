from src.media.backend.player import AbstractMediaPlayer


class FairQueue:
    def __init__(self) -> None:
        self.items = []
        self.count = 0

    def push(self, item):
        assert isinstance(item, AbstractMediaPlayer)
        for idx, (elem_2, _) in enumerate(self.items):
            if item == elem_2:
                self._increase_item(idx)
                break
        else:
            self.append_new_item(item)
        # print(self.items)

    def append_new_item(self, item):
        self.items.append([item, 1])
        self.count += 1

    def _pop_item(self, idx):
        elem, _ = self.items[idx]

        # decreasing item
        self.items[idx][1] -= 1
        self.count -= 1

        # deleting if item empty
        if self.items[idx][1] == 0:
            del self.items[idx]

        return elem

    def _increase_item(self, idx):
        self.items[idx][1] += 1
        self.count += 1

    def pop(self):
        if self.has_elements():
            max_idx = 0
            max_ratio = 0

            for idx, (elem, count) in enumerate(self.items):
                fps = elem.fps
                ratio = (
                    count / fps
                )  # the higher the ratio, the earlier the update is required
                if ratio > max_ratio:
                    max_idx = idx
                    max_ratio = ratio

            # pop element with highest ratio, and return it
            return self._pop_item(max_idx)
        else:
            return None

    def has_elements(self):
        return self.count > 0

    def remove_item(self, item):
        for idx, (it, _) in enumerate(self.items):
            if item == it:
                self.count -= self.items[idx][1]
                del self.items[idx]
                break

    def clear(self):
        self.items = []
        self.count = 0

    def __len__(self):
        return self.count
