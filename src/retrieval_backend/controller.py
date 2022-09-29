import logging
import time
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import numpy as np
from scipy import spatial

from src.data_classes import Sample, Annotation
from src.qt_helper_widgets.histogram import Histogram_Widget
from src.qt_helper_widgets.lines import QHLine
from src.qt_helper_widgets.display_scheme import QShowAnnotation
from src.dialogs.annotation_dialog import QAnnotationDialog
from src.retrieval_backend.filter import FilterCriteria
from src.retrieval_backend.interval import Interval
from src.retrieval_backend.query import Query
from src.retrieval_backend.filter_dialog import QRetrievalFilter
from src.retrieval_backend.mode import RetrievalMode
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
        # Controll attributes
        self._query: Query = None
        self._annotation = None
        self._current_interval = None
        self._interval_size: int = None
        self._overlap: float = None
        self._open_dialog: qtw.QDialog = None
        self.TRIES_PER_INTERVAL = 3
        self.init_UI()
        self.enabled = False
        self.setEnabled(False)

    def init_UI(self):
        self.retrieval_options = qtw.QComboBox()
        for x in RetrievalMode:
            name = x.name.capitalize()
            self.retrieval_options.addItem(name)
        self.retrieval_options.currentIndexChanged.connect(self.update_retrieval_mode)

        self.retrieval_options_widget = qtw.QWidget()
        self.retrieval_options_widget.setLayout(qtw.QHBoxLayout())
        self.retrieval_options_widget.layout().addWidget(qtw.QLabel("Mode:"))
        self.retrieval_options_widget.layout().addWidget(
            self.retrieval_options, stretch=1
        )

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

        self.decline_button = qtw.QPushButton("DECLINE", self)
        self.decline_button.clicked.connect(self.decline_interval)
        self.button_group.layout().addWidget(self.decline_button)

        self.similarity_label = qtw.QLabel(self)
        self.progress_label = qtw.QLabel(format_progress(0, 0), self)

        self.footer_widget = qtw.QWidget()
        self.footer_widget.setLayout(qtw.QGridLayout())
        self.footer_widget.layout().addWidget(qtw.QLabel("Similarity", self), 0, 0)
        self.footer_widget.layout().addWidget(self.similarity_label, 0, 1)

        self.footer_widget.layout().addWidget(qtw.QLabel("Progress:", self), 1, 0)
        self.footer_widget.layout().addWidget(self.progress_label, 1, 1)

        vbox = qtw.QVBoxLayout()

        vbox.addWidget(self.retrieval_options_widget)
        vbox.addWidget(QHLine())
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

    def load_state(self, state):
        self._annotation = state
        self._current_interval = None
        self._interval_size = 100  # TODO: Import from settings
        self._overlap = 0.66  # TODO: Import from settings
        intervals = self.generate_intervals()
        self._query = Query(intervals)
        # load correct mode
        idx = self.retrieval_options.currentIndex()
        self._query.change_mode(RetrievalMode(idx))
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
        for sample in self._annotation.samples:
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
        logging.info(f"GENERATING INTERVALS TOOK {end_time - start_time}ms")
        return intervals

    def update_retrieval_mode(self):
        idx = self.retrieval_options.currentIndex()
        new_mode = RetrievalMode(idx)
        if self._query is not None:
            self._query.change_mode(new_mode)
            self.load_next()

    def get_intervals_in_range(self, lower, upper):
        intervals = []
        start = lower

        stepsize = self.get_stepsize()
        logging.info(f"{stepsize = }")

        get_end = lambda x: x + self._interval_size - 1
        get_start = lambda x: max(
            min(upper - self._interval_size + 1, x + stepsize), x + 1
        )

        if get_end(start) > upper:
            logging.warning("sample too short -> cannot create any interval")

        while get_end(start) <= upper:
            end = get_end(start)

            for i in self.get_predictions(start, end):
                intervals.append(i)
            start = get_start(start)

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
        if self._annotation.dataset.dependencies_exist:
            return True, np.array(self._annotation.dataset.dependencies)
        else:
            return False, None

    def get_stepsize(self):
        return max(
            1, min(int(self._interval_size * (1 - self._overlap)), self._interval_size)
        )

    # TODO: actually use a network, currently only proof of concept
    def run_network(self, lower, upper):
        array_length = len(self.scheme)
        return np.random.rand(array_length)

    # Display the current interval to the user: Show him the Interval boundaries and the predicted annotation
    def update_UI(self):
        if self._query is None:
            self.progress_label.setText("_/_")
        else:
            txt = format_progress(self._query.idx, len(self._query))
            self.progress_label.setText(txt)

            filter_active_txt = (
                "Inactive" if self._query.filter_criterion.is_empty() else "Active"
            )
            self.filter_active.setText(filter_active_txt)

        if self._current_interval is None:
            self.similarity_label.setText("_")
            self.main_widget.show_annotation(None)
        else:
            self.similarity_label.setText(f"{self._current_interval.similarity :.3f}")
            proposed_annotation = self._current_interval.annotation
            self.main_widget.show_annotation(proposed_annotation)

    @qtc.pyqtSlot(bool)
    def modify_filter_clicked(self, _):
        if self._open_dialog:
            self.refocus_dialog()
        else:
            filter_criterion = (
                self._query.filter_criterion
                if self._query is not None
                else FilterCriteria()
            )

            self._open_dialog = QRetrievalFilter(filter_criterion, self.scheme)
            self._open_dialog.filter_changed.connect(self.change_filter)
            self._open_dialog.finished.connect(self.free_dialog)
            self._open_dialog.open()

    def change_filter(self, filter_criteria):
        if self._query is not None:
            self._query.change_filter(filter_criteria)
            logging.info(f"change filter {len(self._query) = }")
            self.update_UI()
            self.load_next()

    # same as manually_annotate_interval except that the annotation is preloaded with the suggested annotation
    def modify_interval_prediction(self):
        if self._open_dialog:
            self.refocus_dialog()
        if self._current_interval is None:
            return
            # TODO maybe find better solution
        else:
            sample = self.current_sample

            dialog = QAnnotationDialog(self.scheme, self.dependencies)
            dialog.finished.connect(self.free_dialog)

            dialog.new_annotation.connect(self.modify_interval)
            self._open_dialog = dialog
            dialog.open()

            dialog._set_annotation(sample.annotation)

    def modify_interval(self, new_annotation):
        interval = self._current_interval
        interval.annotation = new_annotation
        self.update_UI()

    # accept the prediction from the network -> mark the interval as done
    def accept_interval(self):
        if self._current_interval:
            assert self._query is not None
            self._query.mark_interval(self._current_interval)
            self.load_next()
        else:
            # TODO
            logging.info("IM ELSE BLOCK")

    # don't accept the prediction
    def decline_interval(self):
        self.load_next()

    def load_next(self):
        assert self._query is not None
        if self._query.has_next():
            old_interval = self._current_interval
            self._current_interval = self._query.get_next()
            if old_interval != self._current_interval:
                # only emit new loop if the interval has changed remember that for each interval there might be
                # multiple predictions that get testet one after another
                l, r = self._current_interval.start, self._current_interval.end
                self.start_loop.emit(l, r)
        else:
            self._current_interval = None
        self.update_UI()

    @qtc.pyqtSlot(RetrievalMode)
    def change_mode(self, mode):
        if self._query is not None:
            self._query.change_mode(mode)
            self.load_next()

    @accepts(object, bool)
    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.retrieval_options.setEnabled(enabled)
        self.modify_button.setEnabled(enabled)
        self.modify_filter.setEnabled(enabled)
        self.accept_button.setEnabled(enabled)
        self.decline_button.setEnabled(enabled)

    def refocus_dialog(self):
        # this will remove minimized status
        # and restore window with keeping maximized/normal state
        self._open_dialog.setWindowState(
            self._open_dialog.windowState() & ~qtc.Qt.WindowMinimized
            | qtc.Qt.WindowActive
        )

        # this will activate the window
        self._open_dialog.activateWindow()

    @qtc.pyqtSlot(int)
    def free_dialog(self, x):
        self._open_dialog.deleteLater()
        self._open_dialog = None

    @property
    def dependencies(self):
        return self._annotation.dataset.dependencies

    @property
    def scheme(self):
        return self._annotation.dataset.scheme

    @property
    def current_sample(self):
        i = self._current_interval
        sample = Sample(i.start, i.end, i.annotation)
        return sample
