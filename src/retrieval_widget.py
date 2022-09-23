from dataclasses import dataclass, field
import logging
from operator import eq
import time
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
from enum import Enum
import numpy as np
from scipy import spatial

from .data_classes.sample import Sample
from .qt_helper_widgets.lines import QHLine
from .qt_helper_widgets.adaptive_scroll_area import QAdaptiveScrollArea


class RetrievalMode(Enum):
    DEFAULT = 0
    DESCENDING = 1
    RANDOM = 2


@dataclass(frozen=True)
class Interval:
    start: int = field(hash=True, compare=True)
    end: int = field(hash=True, compare=True)
    predicted_classification: np.ndarray = field(hash=False, compare=False)
    similarity: float = field(hash=False, compare=False)


@dataclass(frozen=True)
class FilterCriteria:
    filter_array: np.ndarray

    # test whether a given interval matches the criterion
    def matches(self, i):
        comp_array = i.predicted_classification
        tmp = np.logical_and(comp_array, self.filter_array)
        res = np.array_equal(self.filter_array, tmp)
        return res

    def __eq__(self, other):
        if isinstance(other, FilterCriteria):
            return np.array_equal(self.filter_array, other.filter_array)
        return False


class Query:
    def __init__(self, intervals: list) -> None:
        self._intervals = intervals
        self._indices = []  # for querying
        self._idx = -1
        self._marked_intervals = set()  # for marking intervals as DONE
        self._mode: RetrievalMode = RetrievalMode.DEFAULT
        self._filter_criteria: FilterCriteria = None

        self.debug_count = 0

        self.update_indices()

    def __len__(self):
        return len(self._indices)

    def get_next(self) -> Interval:
        assert self.has_next()
        next_unmarked_idx = self.get_next_unmarked_idx()
        self._idx = next_unmarked_idx

        index_to_interval = self._indices[next_unmarked_idx]
        interval = self._intervals[index_to_interval]
        return interval

    def has_next(self):
        return self.get_next_unmarked_idx() < len(self._indices)

    def get_next_unmarked_idx(self):
        idx = self._idx + 1
        while idx < len(self._indices):
            index_to_interval = self._indices[idx]
            if self._intervals[index_to_interval] not in self._marked_intervals:
                break
            idx += 1
        return idx

    def apply_filter(self):
        if self._filter_criteria:
            indices = []
            for idx in range(len(self._intervals)):
                if self._intervals[idx] in self._marked_intervals:
                    continue
                if self._filter_criteria is None or self._filter_criteria.matches(
                    self._intervals[idx]
                ):
                    indices.append(idx)
        else:
            indices = list(range(len(self._intervals)))
        self._indices = indices

    def reorder_indices(self):
        if self._mode == RetrievalMode.DESCENDING:
            print("CHANGING TO DESCENDING")
            ls = [
                (idx, self._intervals[idx].similarity) for idx in self._indices
            ]  # zip indices with similarities

            ls = sorted(ls, key=lambda x: x[1], reverse=True)  # Sorting by similarity
            self._indices = [x for x, _ in ls]

        if self._mode == RetrievalMode.DEFAULT:
            print("CHANGING TO DEFAULT")
            self._indices.sort()
        if self._mode == RetrievalMode.RANDOM:
            print("CHANGING TO RANDOM")
            perm = np.random.permutation(np.array(self._indices))
            self._indices = list(perm)

    def update_indices(self):
        self.apply_filter()
        self.reorder_indices()
        self._idx = -1

    # modify _indices to only include those that match the filter criterium
    def change_filter(self, criteria: FilterCriteria):
        start = time.time()
        reason_1 = self._filter_criteria is None and criteria is not None
        reason_2 = self._filter_criteria is not None and criteria is None
        reason_3 = self._filter_criteria != criteria
        if reason_1 or reason_2 or reason_3:
            self._filter_criteria = criteria
            self.update_indices()
        end = time.time()
        print(f"CHANGE_FILTER TOOK {end - start}ms")

    # reorder the indices
    def change_mode(self, mode: RetrievalMode):
        start = time.time()
        if mode != self._mode:
            self._mode = mode
            self.update_indices()
        end = time.time()
        print(f"CHANGE_MODE TOOK {end - start}ms")

    def mark_as_done(self, i: Interval):
        assert i not in self._marked_intervals
        self._marked_intervals.add(i)
        self.debug_count += 1
        print(self.debug_count)

    @property
    def idx(self):
        return self._idx


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
        self.TRIES_PER_INTERVAL = 3
        self.init_layout()

    def format_progress(self, x, y):
        percentage = int(x * 100 / y) if y != 0 else 0
        return f"{x : }/{y}\t[{percentage}%] "

    def init_layout(self):
        self.scroll_widgets = []

        self.header_widget = qtw.QLabel(
            "CURRENT PREDICTION", alignment=qtc.Qt.AlignCenter
        )

        self.main_widget = qtw.QWidget()
        self.main_widget.setLayout(qtw.QHBoxLayout())

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
        self.progress_label = qtw.QLabel(self.format_progress(0, 0), self)

        self.footer_widget = qtw.QWidget()
        self.footer_widget.setLayout(qtw.QGridLayout())
        self.footer_widget.layout().addWidget(qtw.QLabel("Similarity", self), 0, 0)
        self.footer_widget.layout().addWidget(self.similarity_label, 0, 1)

        self.footer_widget.layout().addWidget(qtw.QLabel("Progress:", self), 1, 0)
        self.footer_widget.layout().addWidget(self.progress_label, 1, 1)

        vbox = qtw.QVBoxLayout()
        vbox.addWidget(self.header_widget, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.main_widget, alignment=qtc.Qt.AlignCenter, stretch=1)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.button_group, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.footer_widget, alignment=qtc.Qt.AlignCenter)
        self.setLayout(vbox)
        self.setMinimumWidth(300)

    def load_annotation(self, a):
        if not a.dataset.dependencies_exist:
            raise RuntimeError

        self._annotation = a
        self._current_interval = None
        self._interval_size = 100  # TODO: Import from settings
        self._overlap = 0  # TODO: Import from settings
        intervals = self.generate_intervals()
        self._query = Query(intervals)
        self.load_next()

    # initialize the intervals from the given annotation
    # TODO REWORK -> Currently just prove of concept
    # REWORK = ONLY get intervals inside samples that are currently not annotated!
    # Maybe just loop through the sample, and grab all unannotated ones
    def generate_intervals(self):
        start_time = time.time()
        print("STARTING TO GENERATE INTERVALS")

        intervals = []
        start = 0
        N = self._annotation.frames

        COMBINATIONS = np.array(self._annotation.dataset.dependencies)
        while start < N:
            end = min(N - 1, start + self._interval_size)

            predicted_attributes = self.get_prediction_for_interval(start, end)

            DIST = spatial.distance.cdist(COMBINATIONS, predicted_attributes, "cosine")
            DIST = DIST.flatten()

            indices = np.argsort(DIST)
            for idx in indices[: self.TRIES_PER_INTERVAL]:
                proposed_classification = COMBINATIONS[idx]
                similarity = 1 - DIST[idx]

                interval = Interval(start, end, proposed_classification, similarity)
                intervals.append(interval)

            start = end + 1
        end_time = time.time()
        logging.info(f"GENERATING INTERVALS TOOK {end_time - start_time}ms")
        return intervals

    def get_prediction_for_interval(self, lower, upper):
        COMBINATIONS = np.array(self._annotation.dataset.dependencies)
        array_length = len(COMBINATIONS[0])
        return np.random.randint(2, size=(1, array_length))

    # Display the current interval to the user: Show him the Interval boundaries and the predicted annotation, start the loop,
    def display_interval(self):
        if self._query:
            txt = self.format_progress(self._query.idx, len(self._query))
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
            widget = qtw.QWidget(self)
            grid = qtw.QGridLayout()
            grid.setColumnStretch(1, 1)

            offset = 0
            for idx, (group_name, group_elements) in enumerate(self.scheme):
                scroll_wid = QAdaptiveScrollArea(self)

                for elem_idx, elem in enumerate(group_elements):
                    adjusted_idx = offset + elem_idx
                    if (
                        self._current_interval.predicted_classification[adjusted_idx]
                        == 1
                    ):
                        lbl = qtw.QLabel(elem, alignment=qtc.Qt.AlignCenter)
                        lbl.setAlignment(qtc.Qt.AlignCenter)
                        scroll_wid.addItem(lbl)
                offset += len(group_elements)

                txt = group_name.upper() + ":"
                name_label = qtw.QLabel(txt)

                grid.addWidget(name_label, idx, 0)
                grid.addWidget(scroll_wid, idx, 1)

            widget.setLayout(grid)

            self.layout().replaceWidget(self.main_widget, widget)
            self.main_widget.setParent(None)
            self.main_widget = widget

    # ask user for manual annotation -> used as a last option kind of thing or also whenever the user feels like it is needed
    def manually_annotate_interval(self):
        pass

    # same as manually_annotate_interval except that the annotation is preloaded with the suggested annotation
    def modify_interval_prediction(self):
        pass

    # accept the prediction from the network -> mark the interval as done
    def accept_interval(self):
        if self._current_interval:
            assert self._query is not None
            self._query.mark_as_done(self._current_interval)
            self.load_next()
        else:
            logging.info("IM ELSE BLOCK")

    # dont accept the prediction
    def decline_interval(self):
        self.load_next()

    # TODO
    def all_intervals_done(self):
        self._current_interval = None
        if self._query:
            N = len(self._query)
            self.progress_label.setText(self.format_progress(N, N))

    def load_next(self):
        if self._query:
            if self._query.has_next():
                old_interval = self._current_interval
                self._current_interval = self._query.get_next()
                self.display_interval()
                if old_interval != self._current_interval:
                    # only emit new loop if the interval has changed
                    # remember that for each interval there might be multiple predictions that get testet one after another
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

    @qtc.pyqtSlot(FilterCriteria)
    def change_filter(self, f):
        if self._query:
            self._query.change_filter(f)

    @property
    def scheme(self):
        return self._annotation.dataset.scheme


if __name__ == "__main__":
    intervals = []
    start = 0

    array_length = 500
    N_intervals = 100000
    step_size = 100

    expected = np.random.randint(2, size=array_length)
    cos_sim = lambda x, y: 1 - spatial.distance.cosine(x, y)

    for _ in range(N_intervals):
        end = start + step_size - 1
        x = np.random.randint(2, size=array_length)
        interval = Interval(start, end, x, cos_sim(expected, x))
        start = end + 1
        intervals.append(interval)

    query = Query(intervals)

    while query.has_next():
        x = query.get_next()
        if query.idx % 4 == 0:
            query.mark_as_done(x)

    query.change_mode(RetrievalMode.DEFAULT)
    # for _ in range(10):
    #    print(query.idx, query._indices[query.idx], query.get_next())
    print(f"{len(query) = }")
    query.change_mode(RetrievalMode.DESCENDING)
    # for _ in range(10):
    #    print(query.idx, query._indices[query.idx], query.get_next())
    print(f"{len(query) = }")
    query.change_mode(RetrievalMode.RANDOM)
    # for _ in range(10):
    #    print(query.idx, query._indices[query.idx], query.get_next())
    print(f"{len(query) = }")

    filter_array = np.zeros(array_length)
    filter_array[0] = 1
    filter_array[1] = 1
    filter_array[2] = 1

    filter = FilterCriteria(filter_array)

    print(f"Before filter: {len(query) = }")
    query.change_filter(filter)
    print(f"After filter: {len(query) = }")
