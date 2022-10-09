from copy import deepcopy

from src.annotation.annotation_base import AnnotationBaseClass
from src.annotation.retrieval.main_widget import QRetrievalWidget
from src.data_classes import Sample


class RetrievalAnnotation(AnnotationBaseClass):

    # TDOD
    def __init__(self):
        super(RetrievalAnnotation, self).__init__()
        self.main_widget = QRetrievalWidget()

        # Constants
        self.TRIES_PER_INTERVAL = 3
        self._interval_size: int = 100
        self._overlap: float = 0

    def undo(self):
        pass

    def redo(self):
        pass

    def annotate(self):
        pass

    def cut(self):
        pass

    def cut_and_annotate(self):
        pass

    def merge(self, left):
        pass

    def insert_sample(self, new_sample):
        assert len(self.samples) > 0

        left = (
            None  # index to the rightmost sample with: new_sample.lower >= left.lower
        )
        right = (
            None  # index to the leftmost sample with: new_sample.upper <= right.lower
        )

        # grab those indices
        for idx, s in enumerate(self.samples):
            if s.start_position <= new_sample.start_position <= s.end_position:
                left = idx
            if s.start_position <= new_sample.end_position <= s.end_position:
                right = idx
            if s.start_position > new_sample.end_position:
                break

        # must not be the case
        assert left is not None and right is not None

        # grab all samples that share some common frame-positions with the new sample
        tmp = [self.samples[idx] for idx in range(left, right + 1)]

        # remove all of them from the sample-list
        for s in tmp:
            self.samples.remove(s)

        # create new left_sample
        left_sample = Sample(
            tmp[0].start_position,
            new_sample.start_position - 1,
            deepcopy(tmp[0].annotation),
        )

        # only add it if it is valid
        if left_sample.start_position <= left_sample.end_position:
            self.samples.append(left_sample)

        # create new right sample
        right_sample = Sample(
            new_sample.end_position + 1,
            tmp[-1].end_position,
            deepcopy(tmp[-1].annotation),
        )

        # only add it if it is valid
        if right_sample.start_position <= right_sample.end_position:
            self.samples.append(right_sample)

        # add new sample if it is valid
        if new_sample.start_position <= new_sample.end_position:
            self.samples.append(new_sample)

        # reorder samples -> the <= 3 newly added samples were appended to the end
        self.samples.sort()

        # merge neighbors with same annotation -> left_neighbor must not be the same as left_sample previously,
        # same for right neighbor
        idx = self.samples.index(new_sample)
        # only if the new sample is not the first list element
        if idx > 0:
            left_neighbor = self.samples[idx - 1]
            if left_neighbor.annotation == new_sample.annotation:
                self.samples.remove(left_neighbor)
                new_sample.start_position = left_neighbor.start_position
        # only if the new sample is not the last list element
        if idx < len(self.samples) - 1:
            right_neighbor = self.samples[idx + 1]
            if right_neighbor.annotation == new_sample.annotation:
                self.samples.remove(right_neighbor)
                new_sample.end_position = right_neighbor.end_position

        # update samples and notify timeline etc.
        self.check_for_selected_sample(force_update=True)

    def add_to_undo_stack(self):
        pass

    # TODO
    def load_subclass(self):
        self.main_widget.load()
