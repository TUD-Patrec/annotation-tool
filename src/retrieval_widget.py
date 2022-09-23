from dataclasses import dataclass
import logging
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import enum
import numpy as np

from .data_classes.sample import Sample


class RetrievalMode(enum):
    DEFAULT = 0
    RANDOM = 1
    DESCENDING = 2
    QUERY = 3


@dataclass(frozen=True)
class Interval:
    start: int
    end: int
    predicted_classification: np.ndarray
    similarity: float


@dataclass(frozen=True)
class FilterCriteria:
    filter_array: np.ndarray

    # test whether a given interval matches the criterion
    def matches(self, i):
        pass


class Query:
    def __init__(self) -> None:
        self._filter_criteria = None
        self._intervalls = []
        self._indices = []  # for querying
        self._marked_intervals = set()  # for marking intervals as DONE
        self._mode: RetrievalMode = None

    def __iter__(self):
        if self.has_next():
            pass
        else:
            raise StopIteration
        pass

    def __next__(self) -> Interval:
        pass

    def has_next(self):
        pass

    def interval_to_sample(self, x):
        pass

    def order_intervals(self, mode: RetrievalMode):
        pass

    # modify _indices to only include those that match the filter criterium
    def apply_filter(self, criteria: FilterCriteria):
        # only if mode == QUERY
        pass

    # reorder the indices
    def mode_changed(self, mode: RetrievalMode):
        pass

    def mark_as_done(self, i: Interval):
        self._marked_intervals.add(i)


class QRetrievalWidget(qtw.QWidget):
    new_sample = qtc.pyqtSignal(Sample)
    start_loop = qtc.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(QRetrievalWidget, self).__init__(*args, **kwargs)
        # Controll attributes
        self.query: Query = None
        self.current_interval = None
        self._overlap: float = 0
        self._window_size: int = None
        self.init_layout()

    def init_layout(self):
        pass

    def load_annotation(self, a):
        pass

    # initialize the intervals from the given annotation
    def init_intervals(self):
        pass

    # Display the current interval to the user: Show him the Interval boundaries and the predicted annotation, start the loop,
    def display_interval(self):
        pass

    # ask user for manual annotation -> used as a last option kind of thing or also whenever the user feels like it is needed
    def manually_annotate_interval(self):
        pass

    # same as manually_annotate_interval except that the annotation is preloaded with the suggested annotation
    def modify_interval_prediction(self):
        pass

    # accept the prediction from the network -> mark the interval as done
    def accept_interval(self):
        pass

    # dont accept the prediction
    def decline_interval(self):
        pass

    # Main function
    def retieval(self):
        pass

    @qtc.pyqtSlot()
    def settings_changed(self):
        pass

    @qtc.pyqtSlot(RetrievalMode)
    def change_mode(self, mode):
        pass

    @qtc.pyqtSlot(FilterCriteria)
    def change_filter(self, f):
        pass
