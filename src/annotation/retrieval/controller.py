from copy import deepcopy
import logging
from typing import List, Tuple

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw
import numpy as np

from src.annotation.annotation_base import AnnotationBaseClass
from src.annotation.modes import AnnotationMode
from src.annotation.retrieval.main_widget import QRetrievalWidget
from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.annotation.retrieval.retrieval_backend.filter import FilterCriterion
from src.annotation.retrieval.retrieval_backend.filter_dialog import QRetrievalFilter
from src.annotation.retrieval.retrieval_backend.loader import RetrievalLoader
from src.annotation.retrieval.retrieval_backend.query import Query
from src.annotation.retrieval.tool_widget import RetrievalTools
from src.data_model import Sample
from src.dialogs.annotation_dialog import QAnnotationDialog
from src.settings import settings


class RetrievalAnnotation(AnnotationBaseClass):
    update_UI = qtc.pyqtSignal(Query, object)

    def __init__(self):
        super().__init__()

        self.mode = AnnotationMode.RETRIEVAL

        self.main_widget = QRetrievalWidget()

        # tool widget
        self.tool_widget = RetrievalTools()
        self.tool_widget.accept_interval.connect(self.accept)
        self.tool_widget.modify_interval.connect(self.modify)
        self.tool_widget.reject_interval.connect(self.reject)
        self.tool_widget.change_filter.connect(self.select_filter)

        # Constants
        self.interval_size: int = settings.retrieval_segment_size
        self.overlap: float = settings.retrieval_segment_overlap

        # Control Attributes
        self.filter_criterion: FilterCriterion = FilterCriterion()  # empty filter
        self.classifications: np.ndarray = None  # maybe needed later
        self.intervals: List[Tuple[int, int]] = None  # maybe needed later
        self.query: Query = None
        self.current_element: RetrievalElement = None

        # GUI widget
        self.main_widget = QRetrievalWidget()
        self.update_UI.connect(self.main_widget.update_UI)

    def load_subclass(self):
        """Load the data for the retrieval mode."""
        self.loading_thread = RetrievalLoader(self)
        self.loading_thread.success.connect(self.loading_success)
        self.loading_thread.error.connect(self.loading_error)

        self.progress_dialog = qtw.QProgressDialog(self.main_widget)
        # remove cancel button of progress_dialog
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setWindowFlag(qtc.Qt.WindowCloseButtonHint, False)
        self.progress_dialog.setWindowFlag(qtc.Qt.WindowContextHelpButtonHint, False)
        self.progress_dialog.setLabelText("Loading intervals...")
        self.progress_dialog.setWindowTitle("Loading")
        self.progress_dialog.setForegroundRole(qtg.QPalette.Highlight)
        self.loading_thread.progress.connect(self.progress_dialog.setValue)
        self.loading_thread.finished.connect(self.progress_dialog.close)
        self.progress_dialog.open()
        self.loading_thread.start()

    @qtc.pyqtSlot(Exception)
    def loading_error(self, e: Exception):
        """This method is called when the loading thread has failed loading the data."""
        logging.error(repr(e))

        msg = qtw.QMessageBox()
        msg.setIcon(qtw.QMessageBox.Critical)
        msg.setText("Running the network failed!")
        txt = "Retrieval Mode could not be loaded.\nCheck if the network is actually loaded and reload after!"  # noqa: E501
        msg.setInformativeText(txt)
        msg.setWindowTitle("Error")
        msg.exec_()

        self.setEnabled(False)

    @qtc.pyqtSlot(list, np.ndarray, list)
    def loading_success(
        self,
        intervals: List[Tuple],
        classifications: np.ndarray,
        retrieval_elements: List[RetrievalElement],
    ):
        """This method is called when the loading thread has finished loading the data."""
        self.intervals = intervals
        self.classifications = classifications
        self.query = Query(retrieval_elements)

        self.load_next()
        self.setEnabled(True)

    def load_next(self):
        """Load the next element in the query."""
        if self.query:
            self.current_element = next(self.query)
            if self.current_element is not None:
                i = self.current_element.i  # index of the element
                l, r = self.intervals[i]
                self.start_loop.emit(l, r)  # start the loop
        self.update_UI.emit(self.query, self.current_element)

    # Slots
    @qtc.pyqtSlot()
    def select_filter(self):
        if self.enabled and self.scheme:
            dialog = QRetrievalFilter(self.filter_criterion, self.scheme)
            dialog.filter_changed.connect(self.new_filter)
            self.open_dialog(dialog)

    @qtc.pyqtSlot()
    def modify(self):
        if self.enabled:
            if self.current_element:
                dialog = QAnnotationDialog(
                    self.current_element, self.scheme, self.dependencies
                )
                dialog.finished.connect(lambda _: self.element_changed())
                self.open_dialog(dialog)
            else:
                self.update_UI.emit(self.query, self.current_element)

    @qtc.pyqtSlot()
    def accept(self):
        if self.enabled:
            if self.current_element:
                self.query.accept(self.current_element)
                self.add_new_element(self.query.accepted_elements, self.current_element)
                self.load_next()
            else:
                self.update_UI.emit(self.query, self.current_element)

    @qtc.pyqtSlot()
    def reject(self):
        if self.enabled:
            if self.current_element:
                self.query.reject(self.current_element)
                self.load_next()
            else:
                self.update_UI.emit(self.query, self.current_element)

    # Class methods
    def new_filter(self, filter_criterion: FilterCriterion):
        if self.query is not None:
            self.query.set_filter(filter_criterion)
            self.load_next()
        self.filter_criterion = filter_criterion

    def add_new_element(
        self, accepted_elements: List[RetrievalElement], new_element: RetrievalElement
    ):
        """
        Adds the new_element to the samples.
        In case of overlapping segments this method will also perform some partitioning and
        majority-voting to produce the desired updated version of the samples list.

        Args:
            accepted_elements: The list of already accepted RetrievalElements.
            new_element: The new RetrievalElement to be added.
        """

        # grab elements with overlapping intervals
        relevant_elements = filter(
            lambda x: x.interval[0] <= new_element.interval[1]
            and x.interval[1] >= new_element.interval[0],
            accepted_elements,
        )
        relevant_elements = list(relevant_elements)  # cast to list
        relevant_intervals = [
            x.interval for x in relevant_elements
        ]  # get intervals of relevant elements

        # segment those intervals into the smallest partitions that are inside the new interval
        set1 = {
            i[0] for i in relevant_intervals if i[0] >= new_element.interval[0]
        }  # left borders
        set2 = {
            i[1] for i in relevant_intervals if i[1] <= new_element.interval[1]
        }  # right borders
        set3 = {
            new_element.interval[0],
            new_element.interval[1],
        }  # borders of new interval  -> actually not needed but for completeness (new_element \in accepted_elements)  # noqa: E501
        all_points = set1.union(set2).union(set3)  # combine all points
        all_points = sorted(all_points)  # sort the points

        partition = [
            (
                all_points[i],
                all_points[i + 1] - 1,
            )  # if not last part decrease right border by 1
            if i < len(all_points) - 2
            else (
                all_points[i],
                all_points[i + 1],
            )  # if last part keep right border
            for i in range(len(all_points) - 1)
        ]  # -> non overlapping partition of the new interval

        for part in partition:
            overlapping_elements = filter(
                lambda x: x.interval[0] <= part[1] and x.interval[1] >= part[0],
                accepted_elements,
            )  # get all objects that overlap with the part

            overlapping_elements = list(overlapping_elements)  # cast to list

            annotations = [
                x.annotation for x in overlapping_elements
            ]  # get the annotations of the overlapping objects

            annotation = max(
                set(annotations), key=annotations.count
            )  # most common annotation (majority vote)

            sample = Sample(*part, annotation)  # create the sample

            self.insert_sample(sample)  # insert the sample

    def insert_sample(self, new_sample: Sample):
        """Inserts the new sample into the samples list."""
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

    def element_changed(self):
        self.update_UI.emit(self.query, self.current_element)

    def step_size(self):
        res = max(
            1,
            min(int(self.interval_size * (1 - self.overlap)), self.interval_size),
        )
        return res
