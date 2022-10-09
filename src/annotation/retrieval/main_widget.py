import logging
import time

import numpy as np
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
from scipy import spatial

from src.annotation.retrieval.retrieval_backend.filter import FilterCriteria
from src.annotation.retrieval.retrieval_backend.filter_dialog import \
    QRetrievalFilter
from src.annotation.retrieval.retrieval_backend.interval import Interval
from src.annotation.retrieval.retrieval_backend.query import Query
from src.data_classes import Annotation, AnnotationScheme, Sample
from src.dialogs.annotation_dialog import QAnnotationDialog
from src.dialogs.dialog_manager import open_dialog
from src.qt_helper_widgets.display_scheme import QShowAnnotation
from src.qt_helper_widgets.histogram import Histogram_Widget
from src.qt_helper_widgets.lines import QHLine
from src.utility.decorators import accepts


def format_progress(x, y):
    x += 1
    percentage = int(x * 100 / y) if y != 0 else 100
    return f"{x : }/{y}\t[{percentage}%] "


class QRetrievalWidget(qtw.QWidget):
    make_sample = qtc.pyqtSignal(Interval)
    start_loop = qtc.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(QRetrievalWidget, self).__init__(*args, **kwargs)

        # Settings controll attributes to default values
        self._query: Query = None
        self._current_interval = None
        self.intervals = None

        self.init_UI()

    def init_UI(self):
        self.filter_widget = qtw.QWidget()
        self.filter_widget.setLayout(qtw.QHBoxLayout())
        self.filter_widget.layout().addWidget(qtw.QLabel("Filter:"))
        self.filter_active = qtw.QLabel("Inactive")
        self.modify_filter = qtw.QPushButton("Select Filter")
        self.modify_filter.clicked.connect(self.modify_filter_clicked)
        self.filter_widget.layout().addWidget(self.filter_active)
        self.filter_widget.layout().addWidget(self.modify_filter)

        self.main_widget = QShowAnnotation(self)

        self.histogram = Histogram_Widget()

        self.button_group = qtw.QWidget()
        self.button_group.setLayout(qtw.QHBoxLayout())

        self.accept_button = qtw.QPushButton("ACCEPT", self)
        self.accept_button.clicked.connect(self.accept_interval)
        self.button_group.layout().addWidget(self.accept_button)

        self.modify_button = qtw.QPushButton("MODIFY", self)
        self.modify_button.clicked.connect(self.modify_interval_prediction)
        self.button_group.layout().addWidget(self.modify_button)

        self.reject_button = qtw.QPushButton("REJECT", self)
        self.reject_button.clicked.connect(self.reject_interval)
        self.button_group.layout().addWidget(self.reject_button)

        self.similarity_label = qtw.QLabel(self)
        self.progress_label = qtw.QLabel(format_progress(0, 0), self)

        self.footer_widget = qtw.QWidget()
        self.footer_widget.setLayout(qtw.QGridLayout())
        self.footer_widget.layout().addWidget(qtw.QLabel("Similarity", self), 0, 0)
        self.footer_widget.layout().addWidget(self.similarity_label, 0, 1)

        self.footer_widget.layout().addWidget(qtw.QLabel("Progress:", self), 1, 0)
        self.footer_widget.layout().addWidget(self.progress_label, 1, 1)

        vbox = qtw.QVBoxLayout()

        vbox.addWidget(self.filter_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.main_widget, alignment=qtc.Qt.AlignCenter, stretch=1)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.histogram)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.button_group, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.footer_widget, alignment=qtc.Qt.AlignCenter)
        self.setLayout(vbox)
        self.setMinimumWidth(300)

    # Display the current interval to the user: Show him the Interval boundaries and the predicted annotation
    def update_UI(self):
        if self._query is None:
            self.progress_label.setText("_/_")
            self.histogram.reset()
            return

        filter_active_txt = (
            "Inactive" if self._query.filter_criterion.is_empty() else "Active"
        )
        self.filter_active.setText(filter_active_txt)

        # Case 1: Query is empty
        if len(self._query) == 0:
            self.progress_label.setText("Empty query")
            self.main_widget.show_annotation(None)
            sim = 0

        # Case 2: We're finished -> End of query reached
        elif self._current_interval is None:
            txt = format_progress(len(self._query) - 1, len(self._query))
            self.progress_label.setText(txt)
            sim = 0

        # Case 3: Default - we're somewhere in the middle of the query
        else:
            txt = format_progress(self._query.idx, len(self._query))
            self.progress_label.setText(txt)

            proposed_annotation = self._current_interval.annotation
            self.main_widget.show_annotation(proposed_annotation)

            sim = self._current_interval.similarity

        data = self._query.similarity_distribution()
        self.similarity_label.setText(f"{sim :.3f}")

        if data.shape[0] > 0:
            self.histogram.plot_data(data, sim)
        else:
            self.histogram.reset()

    def load(self, intervals):
        self.intervals = intervals
        self._query = Query(intervals)
        self.load_next()

    @qtc.pyqtSlot(bool)
    def modify_filter_clicked(self, _):
        filter_criterion = (
            self._query.filter_criterion
            if self._query is not None
            else FilterCriteria()
        )

        dialog = QRetrievalFilter(filter_criterion, self.scheme)
        dialog.filter_changed.connect(self.change_filter)
        open_dialog(dialog)

    def change_filter(self, filter_criteria):
        if self._query is not None:
            self._query.change_filter(filter_criteria)
            self.load_next()

    # same as manually_annotate_interval except that the annotation is preloaded with the suggested annotation
    def modify_interval_prediction(self):
        if self._current_interval:
            sample = self.current_sample

            dialog = QAnnotationDialog(self.scheme, self.dependencies)
            dialog.new_annotation.connect(self.modify_interval)
            open_dialog(dialog)
            dialog._set_annotation(sample.annotation)
        else:
            self.update_UI()

    def modify_interval(self, new_annotation):
        interval = self._current_interval
        interval.annotation = new_annotation
        self.update_UI()

    # accept the prediction from the network -> mark the interval as done
    def accept_interval(self):
        if self._current_interval:
            assert self._query is not None
            self._query.accept_interval(self._current_interval)
            self.check_for_new_sample(self._current_interval)
            self.load_next()
        else:
            self.update_UI()

    # don't accept the prediction
    def reject_interval(self):
        if self._current_interval:
            assert self._query is not None
            self._query.reject_interval(self._current_interval)
            self.load_next()
        else:
            self.update_UI()

    def load_next(self):
        assert self._query is not None
        try:
            old_interval = self._current_interval
            self._current_interval = next(self._query)
            if old_interval != self._current_interval:
                # only emit new loop if the interval has changed remember that for each interval there might be
                # multiple predictions that get tested one after another
                l, r = self._current_interval.start, self._current_interval.end
                self.start_loop.emit(l, r)
        except StopIteration:
            logging.debug("StopIteration reached")
            self._current_interval = None
        self.update_UI()

    def check_for_new_sample(self, interval):
        assert self._query is not None

        # Load sorted intervals
        intervals = sorted(self._query._accepted_intervals)

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
            # filter all intervals that have at least one common frame with one of the windows
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

        # run over annotated windows and do majority-vote
        for w, annotation_list in annotated_windows:
            anno = self.majority_vote(annotation_list)
            if anno:
                sample = Sample(w[0], w[1], anno)
                self.new_sample.emit(sample)

    def majority_vote(self, annotations):
        if len(annotations) > 0:
            max_count = 0
            selected_annotation = None
            for a in annotations:
                count = 0
                for a2 in annotations:
                    if a == a2:
                        count += 1
                assert count > 0
                if count > max_count:
                    max_count = count
                    selected_annotation = a
            return selected_annotation
        else:
            return None

    @accepts(object, bool)
    def setEnabled(self, enabled: bool) -> None:
        self.is_enabled = enabled
        self.modify_button.setEnabled(enabled)
        self.modify_filter.setEnabled(enabled)
        self.accept_button.setEnabled(enabled)
        self.reject_button.setEnabled(enabled)

    @property
    def current_sample(self):
        i = self._current_interval
        sample = Sample(i.start, i.end, i.annotation)
        return sample
