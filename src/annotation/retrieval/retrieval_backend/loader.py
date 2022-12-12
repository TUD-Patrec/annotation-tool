from typing import List, Tuple

import PyQt5.QtCore as qtc
import numpy as np
from scipy import spatial

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.data_model import Annotation
import src.network.controller as network


class RetrievalLoader(qtc.QThread):
    success = qtc.pyqtSignal(list, np.ndarray, list)
    error = qtc.pyqtSignal(Exception)
    progress = qtc.pyqtSignal(int)

    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller

    def run(self):
        intervals, classifications, retrieval_elements = self.load()
        self.success.emit(intervals, classifications, retrieval_elements)
        return
        try:
            intervals, classifications, retrieval_elements = self.load()
            self.success.emit(intervals, classifications, retrieval_elements)
        except Exception as e:
            self.error.emit(e)

    def load(
        self,
    ) -> Tuple[List[Tuple[int, int]], List[np.ndarray], List[RetrievalElement]]:
        # List of intervals (start, end) given by all not-annotated samples using
        # the user defined step- and interval-sizes (see settings dialog).
        # Already annotated samples are not included.
        intervals = create_intervals(
            self.controller.samples,
            self.controller.step_size(),
            self.controller.interval_size,
        )

        # runs the network on each interval and tracks the progress for visualization.
        classifications = get_classifications(intervals, self.progress)

        retrieval_elements = []

        # Dependencies are the attribute representations specified when loading the dataset that are used
        # to fasten the annotation-process by filtering out non-possible attribute combinations.
        attribute_representations = self.controller.dependencies
        if attribute_representations is not None and len(classifications) > 0:
            # Default case: We have attribute representations (="dependencies") and classifications.
            attribute_representations = np.array(
                attribute_representations
            )  # cast to numpy array

            # Compute the distance between each attribute-representation and each classification.
            if attribute_representations.shape[1] == 27:
                # TODO: LAra specific -> remove later
                # Attributes begin at the 8th index of the attribute representation
                dists = spatial.distance.cdist(
                    classifications, attribute_representations[:, 8:], metric="cosine"
                )
            else:
                dists = spatial.distance.cdist(
                    classifications, attribute_representations, metric="cosine"
                )

            for i, interval in enumerate(intervals):
                for j, attr_repr in enumerate(attribute_representations):
                    dist = dists[i, j]
                    annotation = Annotation(self.controller.scheme, np.copy(attr_repr))

                    # RetrievalElements are just wrapped tuples more or less (for convenience)
                    # (see src/annotation/retrieval/retrieval_backend/element.py)
                    elem = RetrievalElement(annotation, interval, dist, i, j)
                    retrieval_elements.append(elem)
        else:
            # This case applies if the loaded dateset does not have any dependencies.
            # Instead of comparing each network-output to the attribute-representations/dependencies
            # we can only compare it to its rounded binarized version (each attribute is rounded to 0 or 1).
            for i, interval in enumerate(intervals):
                attr_repr = np.round(classifications[i])
                dist = spatial.distance.cosine(classifications[i], attr_repr)
                annotation = Annotation(self.controller.scheme, np.copy(attr_repr))
                elem = RetrievalElement(
                    annotation, interval, dist, i, None
                )  # j is None here, because there are no dependencies.
                retrieval_elements.append(elem)

        return intervals, classifications, retrieval_elements


def get_classifications(intervals, progress_callback=None) -> np.ndarray:
    c = []
    for idx, (lo, hi) in enumerate(intervals):
        if progress_callback:
            progress_callback.emit(idx * 100 / len(intervals))
        c.append(run_network(lo, hi))
    return np.array(c)


def run_network(lower, upper):
    return network.run_network(lower, upper + 1)  # upper is inclusive


def create_intervals(samples, step_size, interval_size):
    # collect all bounds of unannotated samples
    bounds = [
        (s.start_position, s.end_position) for s in samples if s.annotation.is_empty()
    ]

    intervals = generate_intervals(bounds, step_size, interval_size)
    return intervals


def create_sub_intervals(intervals, step, interval_size):
    res = []
    for intrvl in intervals:
        res += partition_interval(intrvl, step, interval_size)
    return res


def partition_interval(interval, step, interval_size):
    partitions = []
    lo, hi = interval
    while lo <= hi:
        part = (lo, min(hi, lo + interval_size - 1))
        partitions.append(part)
        lo += step
    return partitions


def interval_cover(intervals):
    intervals.sort()
    res = []
    for tpl in intervals:
        lo = min(tpl)
        hi = max(tpl)
        if len(res) > 0:
            prev_lo, prev_hi = res.pop()
            # merge possible
            if lo <= prev_hi + 1:
                res.append((prev_lo, hi))
            else:
                res.append((prev_lo, prev_hi))
                res.append((lo, hi))
        else:
            res.append((lo, hi))
    return res


def generate_intervals(ranges, step, interval_size):
    if len(ranges) == 0:
        return []

    # generate smallest description of ranges -> merge adjacent tuples
    ranges = interval_cover(ranges)

    # create sub_intervals inside each range
    sub_intervals = create_sub_intervals(ranges, step, interval_size)

    return sub_intervals
