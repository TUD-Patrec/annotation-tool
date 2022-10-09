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
    new_sample = qtc.pyqtSignal(Sample)
    start_loop = qtc.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(QRetrievalWidget, self).__init__(*args, **kwargs)

        # Settings controll attributes to default values
        self._query: Query = None
        self._current_interval = None
        self.is_enabled = False

        #
        self.scheme = None
        self.dependencies = None
        self.n_frames = 0
        self.samples = []

        # Constants
        self.TRIES_PER_INTERVAL = 3
        self._interval_size: int = 100
        self._overlap: float = 0

        self.init_UI()

        self.setEnabled(False)

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

    def load(self, samples, scheme, dependencies, n_frames):
        self._current_interval = None

        self.samples = samples
        self.scheme = scheme
        self.dependencies = dependencies
        self.n_frames = n_frames

        intervals = self.generate_intervals()
        self._query = Query(intervals)
        self.setEnabled(True)
        logging.info(f"State loaded! {len(self._query) = }")
        self.load_next()

    @qtc.pyqtSlot()
    def load_initial_view(self):
        self.load_next()

    # initialize the intervals from the given annotation
    def generate_intervals(self):
        start_time = time.time()

        boundaries = []
        for sample in self.samples:
            # sample already annotated
            if not sample.annotation.is_empty():
                continue

            # only grab samples that are not annotated yet
            l, r = sample.start_position, sample.end_position
            boundaries.append([l, r])

        # merge adjacent intervals
        reduced_boundaries = []
        idx = 0
        while idx < len(boundaries):
            l, r = boundaries[idx]

            nxt_idx = idx + 1
            while nxt_idx < len(boundaries) and boundaries[nxt_idx][0] == r + 1:
                _, r = boundaries[nxt_idx]
                nxt_idx += 1
            reduced_boundaries.append([l, r])
            idx = nxt_idx

        intervals = []
        for l, r in reduced_boundaries:
            tmp = self.get_intervals_in_range(l, r)
            intervals.extend(tmp)

        end_time = time.time()
        logging.debug(f"GENERATING INTERVALS TOOK {end_time - start_time}ms")
        return intervals

    def get_intervals_in_range(self, lower, upper):
        if upper <= lower:
            return []

        intervals = []
        last_intervals = []
        start = lower
        stepsize = self.stepsize()

        while start <= upper:
            end = min(start + self._interval_size - 1, upper)

            if end == upper:
                # 1) if intervals has elements -> extend the last interval to end at the new end-position
                if last_intervals:
                    logging.debug("Extending last interval")
                    for i in last_intervals:
                        i.end = end

                # 2) if intervals is empty -> extend the interval left and right to the needed size for the network
                else:
                    logging.debug("Extending interval left and right")
                    start_adjusted = max(0, start - self._interval_size)
                    end_adjusted = start_adjusted + self._interval_size - 1

                    # find best sourrounding interval
                    while (
                        end_adjusted < self.n_frames - 1
                        and start_adjusted < start - self._interval_size // 2
                    ):
                        start_adjusted += 1
                        end_adjusted += 1

                    # make sure that the adjusted interval is within the video/Mocap
                    if end_adjusted < self.n_frames:
                        preds = self.get_predictions(start_adjusted, end_adjusted)
                        for i in preds:
                            intervals.append(i)
                            i.start = start
                            i.end = end
                    else:
                        logging.warning(
                            f"Was not able to create interval that is small enough to fit inside the video/mocap -> n_frames is smaller than interval_size!"
                        )
            else:
                last_intervals = []
                for i in self.get_predictions(start, end):
                    last_intervals.append(i)
                    intervals.append(i)

            start = start + stepsize

        return intervals

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

    def stepsize(self):
        if hasattr(self, "_stepsize"):
            return self._stepsize
        else:
            step_size = max(
                1,
                min(
                    int(self._interval_size * (1 - self._overlap)), self._interval_size
                ),
            )
            while not self._interval_size % step_size == 0:
                step_size -= 1

            assert step_size / (1 - self._overlap) == self._interval_size
            self._stepsize = step_size
            return step_size
