from copy import deepcopy
import logging
import math
import time

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import numpy as np
from scipy import spatial

from src.annotation.annotation_base import AnnotationBaseClass
from src.annotation.modes import AnnotationMode
from src.annotation.retrieval.main_widget import QRetrievalWidget
from src.annotation.retrieval.retrieval_backend.filter import FilterCriteria
from src.annotation.retrieval.retrieval_backend.filter_dialog import QRetrievalFilter
from src.annotation.retrieval.retrieval_backend.interval import (
    Interval,
    generate_intervals,
)
from src.annotation.retrieval.retrieval_backend.query import Query
from src.dataclasses import Annotation, Sample, Settings
from src.dialogs.annotation_dialog import QAnnotationDialog
from src.network.LARa.lara_specifics import get_annotation_vector
import src.network.controller as network


class RetrievalAnnotation(AnnotationBaseClass):
    update_UI = qtc.pyqtSignal(Query, object)

    def __init__(self):
        super(RetrievalAnnotation, self).__init__()

        self.mode = AnnotationMode.RETRIEVAL

        self.main_widget = QRetrievalWidget()

        # Constants
        self.TRIES_PER_INTERVAL = math.inf
        self.interval_size: int = Settings.instance().retrieval_segment_size
        self.overlap: float = Settings.instance().retrieval_segment_overlap

        # Controll Attributes
        self.query = None
        self.filter_criterion = FilterCriteria()  # empty filter
        self.current_interval = None

        # GUI widget
        self.main_widget = QRetrievalWidget()
        self.update_UI.connect(self.main_widget.update_UI)
        self.main_widget.change_filter.connect(self.change_filter)
        self.main_widget.accept_interval.connect(self.accept_interval)
        self.main_widget.reject_interval.connect(self.reject_interval)
        self.main_widget.modify_interval.connect(self.modify_interval)

    # Slots
    @qtc.pyqtSlot()
    def change_filter(self):
        if self.enabled:
            if self.scheme:
                dialog = QRetrievalFilter(self.filter_criterion, self.scheme)
                dialog.filter_changed.connect(self.new_filter)
                self.open_dialog(dialog)

    @qtc.pyqtSlot()
    def modify_interval(self):
        if self.enabled:
            if self.current_interval:
                dialog = QAnnotationDialog(
                    self.current_interval.as_sample(), self.scheme, self.dependencies
                )
                dialog.finished.connect(lambda _: self.interval_changed())
                self.open_dialog(dialog)
            else:
                self.update_UI.emit(self.query, self.current_interval)

    @qtc.pyqtSlot()
    def accept_interval(self):
        if self.enabled:
            if self.current_interval:
                assert self.query is not None
                self.query.accept_interval(self.current_interval)
                self.check_for_new_sample(self.current_interval)
                self.load_next()
            else:
                self.update_UI.emit(self.query, self.current_interval)

    @qtc.pyqtSlot()
    def reject_interval(self):
        if self.enabled:
            if self.current_interval:
                assert self.query is not None
                self.query.reject_interval(self.current_interval)
                self.load_next()
            else:
                self.update_UI.emit(self.query, self.current_interval)

    # Class methods
    def new_filter(self, filter_criterion):
        if self.query is not None:
            self.query.change_filter(filter_criterion)
            self.load_next()
        self.filter_criterion = filter_criterion

    def check_for_new_sample(self, interval):
        assert self.query is not None
        start = time.perf_counter()

        # Load intervals
        intervals = sorted(self.query._accepted_intervals)

        # get start and end frame-positions
        windows = []
        for idx, intvl in enumerate(intervals):
            if idx == len(intervals) - 1:
                windows.append([intvl.start, intvl.end])
            else:
                next_interval = intervals[idx + 1]
                windows.append([intvl.start, min(intvl.end, next_interval.start)])

        # filter for windows that have at least one common frame with the interval
        windows = list(
            filter(lambda x: x[0] <= interval.end and x[1] >= interval.start, windows)
        )

        annotated_windows = []
        for w in windows:
            # filter all intervals that have at least one common frame
            # with one of the windows
            intervals_in_window = filter(
                lambda x: x.start <= w[0] <= x.end or x.start <= w[1] <= x.end,
                intervals,
            )

            # for each window: store all annotation that were submitted for it
            # this allows for majority-voting
            tmp = []
            for i in intervals_in_window:
                tmp.append(i.annotation)

            # add to annotated_windows
            annotated_windows.append([w, tmp])

        acc1 = 0
        acc2 = 0

        # run over annotated windows and do majority-vote
        for w, annotation_list in annotated_windows:
            t1 = time.perf_counter()
            anno = self.majority_vote(annotation_list)
            t2 = time.perf_counter()
            acc1 += t2 - t1
            if anno:
                sample = Sample(w[0], w[1], anno)
                t3 = time.perf_counter()
                self.insert_sample(sample)
                t4 = time.perf_counter()
                acc2 += t4 - t3
        end = time.perf_counter()
        logging.debug(
            f"check_for_new_sample took {end - start}ms. {acc1 = }ms | {acc2 = }ms."
        )

    def majority_vote(self, annotation):
        if len(annotation) >= 0:
            votes_table = {}
            for anno in annotation:
                if anno.binary_str in votes_table:
                    votes_table[anno.binary_str][1] += 1
                else:
                    votes_table[anno.binary_str] = [anno, 1]
            max_key = max(votes_table, key=lambda x: votes_table.get(x)[1])
            return votes_table[max_key][0]
        else:
            return None

    def load_next(self):
        assert self.query is not None
        try:
            old_interval = self.current_interval
            self.current_interval = next(self.query)
            if old_interval != self.current_interval:
                # only emit new loop if the interval has changed
                # remember that for each interval there might be
                # multiple predictions that get tested one after another
                l, r = self.current_interval.start, self.current_interval.end
                self.start_loop.emit(l, r)
        except StopIteration:
            logging.debug("StopIteration reached")
            self.current_interval = None
        self.update_UI.emit(self.query, self.current_interval)

    def load_subclass(self):
        try:
            intervals = self.load_intervals()
            self.query = Query(intervals)
            self.query.change_filter(self.filter_criterion)
            self.load_next()
        except Exception:
            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Critical)
            msg.setText("Running the network failed!")
            txt = "Retrieval Mode could not be loaded.\nCheck if the network is actually loaded and reload after!"  # noqa: E501
            msg.setInformativeText(txt)
            msg.setWindowTitle("Error")
            msg.exec_()

    def load_intervals(self):
        # collect all bounds of unannotated samples
        bounds = [
            (s.start_position, s.end_position)
            for s in self.samples
            if s.annotation.is_empty()
        ]

        sub_intervals = generate_intervals(bounds, self.stepsize(), self.interval_size)

        intervals = []

        for lo, hi in sub_intervals:
            for pred in self.get_predictions(lo, hi):
                intervals.append(pred)

        return intervals

    def get_predictions(self, lower, upper):
        network_output = self.run_network(lower, upper)  # 1D array, x \in [0,1]^N
        success, combinations = self.get_combinations()
        if success:
            network_output = network_output.reshape(1, -1)

            logging.info(f"{network_output.shape = }, {combinations.shape = }")

            # TODO LARa-special treatment, needs to be redone later
            if combinations.shape[1] == 27:
                n_classes = 8
                dist = spatial.distance.cdist(
                    combinations[:, n_classes:], network_output, "cosine"
                )
            else:
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
            logging.debug(f"{network_output = }")
            proposed_classification = np.round(network_output).astype(np.int8)

            similarity = 1 - spatial.distance.cosine(
                network_output, proposed_classification
            )

            # TODO LARa-special treatment -> needs to be redone later
            if proposed_classification.shape[0] == 19:
                proposed_classification = get_annotation_vector(proposed_classification)

            anno = Annotation(self.scheme, proposed_classification)
            yield Interval(lower, upper, anno, similarity)

    def get_combinations(self):
        if self.dependencies is not None:
            return True, np.array(self.dependencies)
        else:
            return False, None

    def insert_sample(self, new_sample):
        assert len(self.samples) > 0

        indexed_samples = list(zip(self.samples, range(len(self.samples))))

        samples_to_the_left = [
            (x, y)
            for x, y in indexed_samples
            if x.start_position <= new_sample.start_position <= x.end_position
        ]
        assert len(samples_to_the_left) == 1
        left_sample, left_idx = samples_to_the_left[0]

        samples_to_the_right = [
            (x, y)
            for x, y in indexed_samples
            if x.start_position <= new_sample.end_position <= x.end_position
        ]
        assert len(samples_to_the_right) == 1
        right_sample, right_idx = samples_to_the_right[0]

        print(f"{left_idx = }, {right_idx = }")

        # remove
        del self.samples[left_idx : right_idx + 1]

        if left_sample.start_position < new_sample.start_position:
            left_sample = Sample(
                left_sample.start_position,
                new_sample.start_position - 1,
                deepcopy(left_sample.annotation),
            )
            assert (
                left_sample.start_position
                <= left_sample.end_position
                <= new_sample.start_position
            )
            self.samples.append(left_sample)

        if right_sample.end_position > new_sample.end_position:
            right_sample = Sample(
                new_sample.end_position + 1,
                right_sample.end_position,
                deepcopy(right_sample.annotation),
            )
            assert (
                new_sample.end_position
                <= right_sample.start_position
                <= right_sample.end_position
            )
            self.samples.append(right_sample)

        assert new_sample.start_position <= new_sample.end_position
        self.samples.append(new_sample)

        # reorder samples -> the <= 3 newly added samples were appended to the end
        self.samples.sort()
        # merge neighbors with same annotation
        # -> left_neighbor must not be the same as left_sample previously,
        # same for right neighbor
        idx = self.samples.index(new_sample)
        # only if the new sample is not the first list element
        if idx > 0:
            left_neighbor = self.samples[idx - 1]
            if left_neighbor.annotation == new_sample.annotation:
                del self.samples[idx - 1]
                new_sample.start_position = left_neighbor.start_position
        idx = self.samples.index(new_sample)
        # only if the new sample is not the last list element
        if idx < len(self.samples) - 1:
            right_neighbor = self.samples[idx + 1]
            if right_neighbor.annotation == new_sample.annotation:
                del self.samples[idx + 1]
                new_sample.end_position = right_neighbor.end_position

        # update samples and notify timeline etc.
        self.check_for_selected_sample(force_update=True)

    def run_network(self, lower, upper):
        # [lower, upper) is expected to be a range instead of a closed interval
        # -> add 1 to right interval border
        return network.run_network(lower, upper + 1)

    def interval_changed(self):
        self.update_UI.emit(self.query, self.current_interval)

    def stepsize(self):
        res = max(
            1,
            min(int(self.interval_size * (1 - self.overlap)), self.interval_size),
        )
        logging.info(f"{res = }")
        return res
