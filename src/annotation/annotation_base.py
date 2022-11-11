from abc import abstractmethod
from typing import List

import PyQt5.QtCore as qtc
import numpy as np

from src.dataclasses import Annotation, AnnotationScheme, Sample
from src.dialogs.dialog_manager import DialogManager


class AnnotationBaseClass(qtc.QObject, DialogManager):
    start_loop = qtc.pyqtSignal(int, int)
    stop_loop = qtc.pyqtSignal()
    samples_changed = qtc.pyqtSignal(list, Sample)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.enabled = False
        self.mode = None

        # Constants
        self.MAX_UNDO_STACK_SIZE = 50

        # undo-redo behavior
        self.undo_stack = []
        self.redo_stack = []

    # SLOTS
    @qtc.pyqtSlot(list, AnnotationScheme, np.ndarray, int)
    def load(
        self,
        samples: List[Sample],
        scheme: AnnotationScheme,
        dependencies: List[np.ndarray],
        n_frames: int,
    ) -> None:
        """
        Load the annotation scheme and the samples to annotate

        Args:
            samples: List of samples to annotate
            scheme: Annotation scheme
            dependencies: List of dependencies for each sample
            n_frames: Number of frames in the video/mocap file
        """
        self.samples = samples
        self.scheme = scheme
        self.dependencies = dependencies
        self.n_frames = n_frames
        self.position = 0
        self.clear_undo_redo()
        self.check_for_selected_sample(force_update=True)
        self.load_subclass()

    @qtc.pyqtSlot(int)
    def setPosition(self, x: int) -> None:
        """
        Set the current position of the annotation.

        Args:
            x: New position.
        """
        assert 0 <= x, f"{x = }"
        assert self.n_frames == 0 or x < self.n_frames, f"{x = }, {self.n_frames = }"
        if x != self.position:
            self.position = x
            self.check_for_selected_sample()

    @qtc.pyqtSlot(bool)
    def setEnabled(self, x: bool) -> None:
        """
        Set the enabled state of the annotation.

        Args:
            x: New enabled state.
        """
        x = bool(x)
        self.enabled = x

        if self.main_widget is not None:
            self.main_widget.setEnabled(x)
        if self.tool_widget is not None:
            self.tool_widget.setEnabled(x)

    @qtc.pyqtSlot()
    def undo(self) -> None:
        """
        Undo the last action.
        """
        pass

    @qtc.pyqtSlot()
    def redo(self) -> None:
        """
        Redo the last action.
        """
        pass

    @qtc.pyqtSlot()
    def clear_undo_redo(self) -> None:
        """
        Clear the undo and redo stacks.
        """
        self.undo_stack = []
        self.redo_stack = []

    @qtc.pyqtSlot()
    def annotate(self) -> None:
        """
        Annotate the current sample.
        """
        pass

    @qtc.pyqtSlot()
    def cut(self) -> None:
        """
        Split the current sample at the current position.
        """
        pass

    @qtc.pyqtSlot()
    def cut_and_annotate(self) -> None:
        """
        Split the current sample at the current position and annotate the new sample.
        """
        pass

    @qtc.pyqtSlot(bool)
    def merge(self, left: bool) -> None:
        """
        Merge the current sample with the sample on the left or right.

        Args:
            left: Merge with the sample on the left.
        """
        pass

    @qtc.pyqtSlot(Sample)
    def insert_sample(self, new_sample: Sample) -> None:
        """
        Insert a new sample into the list of samples.

        Args:
            new_sample: New sample to insert.
        """
        pass

    # Class methods
    def add_to_undo_stack(self) -> None:
        """
        Add the current state to the undo stack.
        """
        pass

    def update_sample_annotation(
        self, sample: Sample, new_annotation: Annotation
    ) -> None:
        """
        Update the annotation of a sample.

        Args:
            sample: Sample to update.
            new_annotation: New annotation.
        """
        self.add_to_undo_stack()
        sample.annotation = new_annotation
        self.samples_changed.emit(self.samples, self.selected_sample)

    @abstractmethod
    def load_subclass(self) -> None:
        """
        Load the subclass.
        """
        raise NotImplementedError

    def check_for_selected_sample(self, force_update=False) -> None:
        """
        Check if the current position is in a sample and if so, select it.

        Args:
            force_update: Force updating the selected sample.
        """
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
