from abc import abstractmethod

import numpy as np
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.data_classes import AnnotationScheme, Sample


class AnnotationBaseClass(qtc.QObject):
    start_loop = qtc.pyqtSignal(int, int)
    stop_loop = qtc.pyqtSignal()
    samples_changed = qtc.pyqtSignal(list, Sample)

    def __init__(self, *args, **kwargs):
        super(AnnotationBaseClass, self).__init__(*args, **kwargs)

        # Controlled Widgets
        self.main_widget = None
        self.tool_widget = None

        # Controll Attributes
        self.position = 0
        self.n_frames = 0
        self.samples = []
        self.selected_sample = None
        self.scheme = None
        self.dependencies = None
        self.enabled = True
        self.mode = None

        # Constants
        self.MAX_UNDO_STACK_SIZE = 50

        # undo-redo behavior
        self.undo_stack = list()
        self.redo_stack = list()

    # SLOTS
    @qtc.pyqtSlot(list, AnnotationScheme, np.ndarray, int)
    def load(self, samples, scheme, dependencies, n_frames):
        self.samples = samples
        self.scheme = scheme
        self.dependencies = dependencies
        self.n_frames = n_frames
        self.position = 0
        self.clear_undo_redo()
        self.check_for_selected_sample(force_update=True)
        self.load_subclass()

    @qtc.pyqtSlot(int)
    def setPosition(self, x):
        assert 0 <= x, f"{x = }"
        assert self.n_frames == 0 or x < self.n_frames, f"{x = }, {self.n_frames = }"
        if x != self.position:
            self.position = x
            self.check_for_selected_sample()

    @qtc.pyqtSlot(bool)
    def setEnabled(self, x):
        x = bool(x)
        self.enabled = x

        if self.main_widget is not None:
            self.main_widget.setEnabled(x)
        if self.tool_widget is not None:
            self.tool_widget.setEnabled(x)

    @qtc.pyqtSlot()
    @abstractmethod
    def undo(self):
        raise NotImplementedError

    @qtc.pyqtSlot()
    @abstractmethod
    def redo(self):
        raise NotImplementedError

    @qtc.pyqtSlot()
    def clear_undo_redo(self):
        self.undo_stack = []
        self.redo_stack = []

    @qtc.pyqtSlot()
    @abstractmethod
    def annotate(self):
        raise NotImplementedError

    @qtc.pyqtSlot()
    @abstractmethod
    def cut(self):
        raise NotImplementedError

    @qtc.pyqtSlot()
    @abstractmethod
    def cut_and_annotate(self):
        raise NotImplementedError

    @qtc.pyqtSlot(bool)
    @abstractmethod
    def merge(self, left):
        raise NotImplementedError

    @qtc.pyqtSlot(Sample)
    @abstractmethod
    def insert_sample(self, new_sample):
        raise NotImplementedError

    # Class methods
    @abstractmethod
    def add_to_undo_stack(self):
        raise NotImplementedError

    def update_sample_annotation(self, sample, new_annotation):
        self.add_to_undo_stack()
        sample.annotation = new_annotation
        self.samples_changed.emit(self.samples, self.selected_sample)

    @abstractmethod
    def load_subclass(self):
        raise NotImplementedError

    def check_for_selected_sample(self, force_update=False):
        if len(self.samples) > 0:
            # binary search
            lo = 0
            hi = len(self.samples) - 1

            while lo <= hi:
                mid = (lo + hi) // 2
                sample = self.samples[mid]
                if sample.start_position <= self.position <= sample.end_position:
                    break
                elif self.position < sample.start_position:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:
                raise RuntimeError(f"Could not find sample at position {self.position}")

            if force_update or self.selected_sample is not sample:
                self.selected_sample = sample
                self.samples_changed.emit(self.samples, sample)
        else:
            assert self.position == 0
