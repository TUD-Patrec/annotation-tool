import logging
import time
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import numpy as np
from scipy import spatial

from src.data_classes import Sample
from src.qt_helper_widgets.lines import QHLine
from src.qt_helper_widgets.display_scheme import QShowAnnotation
from src.dialogs.annotation_dialog import QAnnotationDialog
from src.retrieval_backend.filter import FilterCriteria
from src.retrieval_backend.interval import Interval
from src.retrieval_backend.query import Query
from src.retrieval_backend.filter_dialog import QRetrievalFilter
from src.retrieval_backend.mode import RetrievalMode


def format_progress(x, y):
    percentage = int(x * 100 / y) if y != 0 else 0
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

    def init_UI(self):
        self.retrieval_options = qtw.QComboBox()
        for x in RetrievalMode:
            name = x.name.capitalize()
            self.retrieval_options.addItem(name)
        self.retrieval_options.currentIndexChanged.connect(self.update_retrieval_mode)

        self.retrieval_options_widget = qtw.QWidget()
        self.retrieval_options_widget.setLayout(qtw.QHBoxLayout())
        self.retrieval_options_widget.layout().addWidget(qtw.QLabel('Mode:'))
        self.retrieval_options_widget.layout().addWidget(self.retrieval_options, stretch=1)

        self.filter_widget = qtw.QWidget()
        self.filter_widget.setLayout(qtw.QHBoxLayout())
        self.filter_widget.layout().addWidget(qtw.QLabel('Filter:'))
        self.filter_active = qtw.QLabel('Inactive')
        self.modify_filter = qtw.QPushButton('Select Filter')
        self.modify_filter.clicked.connect(self.modify_filter_clicked)
        self.filter_widget.layout().addWidget(self.filter_active)
        self.filter_widget.layout().addWidget(self.modify_filter)

        self.main_widget = QShowAnnotation(self)

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
        vbox.addWidget(self.button_group, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.footer_widget, alignment=qtc.Qt.AlignCenter)
        self.setLayout(vbox)
        self.setMinimumWidth(300)

    def load_annotation(self, a):
        self._annotation = a
        self._current_interval = None
        self._interval_size = 100  # TODO: Import from settings
        self._overlap = 0.66  # TODO: Import from settings
        intervals = self.generate_intervals()
        self._query = Query(intervals)
        # load correct mode
        idx = self.retrieval_options.currentIndex()
        self._query.change_mode(RetrievalMode(idx))

    @qtc.pyqtSlot()
    def load_initial_view(self):
        self.load_next()

    # initialize the intervals from the given annotation
    def generate_intervals(self):
        start_time = time.time()
        print("STARTING TO GENERATE INTERVALS")

        boundaries = []
        for sample in self._annotation.samples:
            if sample.annotation_exists:
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
        logging.info(f'NEW ANNOTATION_MODE = {self.retrieval_options.currentIndex()}')
        idx = self.retrieval_options.currentIndex()
        logging.info(f'{idx = }')
        new_mode = RetrievalMode(idx)
        if self._query:
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

                yield Interval(lower, upper, proposed_classification, similarity)
        else:
            # Rounding the output to nearest integers and computing the distance to that
            network_output = network_output.flatten()  # check if actually needed
            proposed_classification = np.round(network_output)
            proposed_classification = proposed_classification.astype(np.int8)
            assert not np.array_equal(network_output, proposed_classification)
            similarity = 1 - spatial.distance.cosine(
                network_output, proposed_classification
            )
            yield Interval(lower, upper, proposed_classification, similarity)

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
        array_length = self.get_scheme_length()
        return np.random.rand(array_length)

    def get_scheme_length(self):
        c = 0
        for _, group_elements in self.scheme:
            c += len(group_elements)
        return c

    # Display the current interval to the user: Show him the Interval boundaries and the predicted annotation,
    # start the loop.
    def display_interval(self):
        if self._query:
            txt = format_progress(self._query.idx, len(self._query))
            self.progress_label.setText(txt)

        if self._current_interval is None:
            self.similarity_label.setText("")
            widget = qtw.QLabel(
                "There is no interval to show yet.", alignment=qtc.Qt.AlignCenter
            )
            self.layout().replaceWidget(self.main_widget, widget)
            self.main_widget.setParent(None)
            self.main_widget = widget

        else:
            self.similarity_label.setText(f"{self._current_interval.similarity :.3f}")

            proposed_annotation = self._current_interval.predicted_classification
            self.main_widget.show_annotation(self.scheme, proposed_annotation)

    @qtc.pyqtSlot(bool)
    def modify_filter_clicked(self, checked):
        if self._open_dialog:
            self.refocus_dialog()
        else:
            self._open_dialog = QRetrievalFilter(None, self.scheme)
            self._open_dialog.filter_changed.connect(self.change_filter)
            self._open_dialog.finished.connect(self.free_dialog)
            self._open_dialog.open()

    def change_filter(self, filter_array):
        if self._query:
            filter_criteria = FilterCriteria(filter_array)
            self._query.change_filter(filter_criteria)

    # ask user for manual annotation -> used as a last option kind of thing or also whenever the user feels like it
    # is needed
    def manually_annotate_interval(self):
        pass

    # same as manually_annotate_interval except that the annotation is preloaded with the suggested annotation
    def modify_interval_prediction(self):
        if self._open_dialog:
            self.refocus_dialog()
        else:
            sample = self.current_sample

            dialog = QAnnotationDialog(self.scheme, self.dependencies)
            dialog.finished.connect(self.free_dialog)
            dialog._set_annotation(sample.annotation)

            dialog.new_annotation.connect(self.modify_interval)
            self._open_dialog = dialog
            dialog.open()

    def modify_interval(self, annotation_dict):
        interval = self._current_interval

        new_prediction = np.zeros_like(self._current_interval.predicted_classification)
        idx = 0
        for gr_name, gr_elems in self.scheme:
            for elem in gr_elems:
                new_prediction[idx] = annotation_dict[gr_name][elem]
                idx += 1

        interval.predicted_classification = new_prediction
        logging.info('Interval modified')
        self.display_interval()

    # accept the prediction from the network -> mark the interval as done
    def accept_interval(self):
        if self._current_interval:
            assert self._query is not None
            self._query.mark_as_done(self._current_interval)
            self.load_next()
        else:
            logging.info("IM ELSE BLOCK")

    # don't accept the prediction
    def decline_interval(self):
        self.load_next()

    # TODO
    def all_intervals_done(self):
        self._current_interval = None
        if self._query:
            N = len(self._query)
            self.progress_label.setText(format_progress(N, N))

    def load_next(self):
        if self._query:
            if self._query.has_next():
                old_interval = self._current_interval
                self._current_interval = self._query.get_next()
                self.display_interval()
                if old_interval != self._current_interval:
                    # only emit new loop if the interval has changed remember that for each interval there might be
                    # multiple predictions that get testet one after another
                    l, r = self._current_interval.start, self._current_interval.end
                    self.start_loop.emit(l, r)
            else:
                logging.info("ALL intervals_done")
                self.all_intervals_done()

    @qtc.pyqtSlot()
    def settings_changed(self):
        pass

    @qtc.pyqtSlot(RetrievalMode)
    def change_mode(self, mode):
        if self._query:
            self._query.change_mode(mode)

    def refocus_dialog(self):
        # this will remove minimized status
        # and restore window with keeping maximized/normal state
        self._open_dialog.setWindowState(
            self._open_dialog.windowState() & ~qtc.Qt.WindowMinimized | qtc.Qt.WindowActive
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
        annotation_dict = dict()

        idx = 0
        for gr_name, elems in self.scheme:
            annotation_dict[gr_name] = dict()
            for elem in elems:
                annotation_dict[gr_name][elem] = i.predicted_classification[idx]
                idx += 1

        logging.info(f'{annotation_dict = }')

        sample = Sample(i.start, i.end, annotation_dict)
        return sample
