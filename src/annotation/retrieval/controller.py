from copy import deepcopy

import numpy as np
from scipy import spatial

from src.annotation.annotation_base import AnnotationBaseClass
from src.annotation.retrieval.main_widget import QRetrievalWidget
from src.annotation.retrieval.retrieval_backend.interval import (
    Interval, generate_intervals)
from src.data_classes import Annotation, Sample


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

    def load_subclass(self):
        self.main_widget.load()
        self.load_intervals()

    def load_intervals(self):
        # collect all boundaries of unannotated samples
        tmp = [
            (s.start_position, s.end_position)
            for s in self.samples
            if s.annotation.is_empty()
        ]

        sub_intervals = generate_intervals(tmp, self.stepsize(), self._interval_size)

        intervals = []

        for lo, hi in sub_intervals:
            for pred in self.get_predictions(lo, hi):
                intervals.append(pred)

    def get_predictions(self, lower, upper):
        network_output = self.run_network(lower, upper)  # 1D array, x \in [0,1]^N
        success, combinations = self.get_combinations()
        if success:
            network_output = network_output.reshape(1, -1)
            dist = spatial.distance.cdist(combinations, network_output, "cosine")
            dist = dist.flatten()

            indices = np.argsort(dist)

            n_tries = min(len(combinations), self.TRIES_PER_INTERVAL)

            for idx in indices[:n_tries]:
                proposed_classification = combinations[idx]
                similarity = 1 - dist[idx]

                anno = Annotation(self.scheme, proposed_classification)

                yield Interval(lower, upper, anno, similarity)
        else:
            # Rounding the output to nearest integers and computing the distance to that
            network_output = network_output.flatten()  # check if actually needed
            proposed_classification = np.round(network_output)
            proposed_classification = proposed_classification.astype(np.int8)
            assert not np.array_equal(network_output, proposed_classification)
            similarity = 1 - spatial.distance.cosine(
                network_output, proposed_classification
            )

            anno = Annotation(self.scheme, proposed_classification)
            yield Interval(lower, upper, anno, similarity)

    def get_combinations(self):
        if self.dependencies is not None:
            return True, np.array(self.dependencies)
        else:
            return False, None

    # TODO: actually use a network, currently only proof of concept
    def run_network(self, lower, upper):
        array_length = len(self.scheme)
        return np.random.rand(array_length)

    def stepsize(self):
        res = max(
            1,
            min(int(self._interval_size * (1 - self._overlap)), self._interval_size),
        )
        return res
