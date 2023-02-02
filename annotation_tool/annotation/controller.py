import enum
from typing import List

import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw
import numpy as np

from annotation_tool.annotation.annotation_base import AnnotationBaseClass
from annotation_tool.annotation.manual.controller import ManualAnnotation
from annotation_tool.annotation.modes import AnnotationMode
from annotation_tool.annotation.retrieval.controller import RetrievalAnnotation
from annotation_tool.data_model import AnnotationScheme, Sample
from annotation_tool.user_actions import AnnotationActions


class AnnotationController(qtc.QObject):
    start_loop = qtc.pyqtSignal(int, int)
    stop_loop = qtc.pyqtSignal()
    pause_replay = qtc.pyqtSignal()
    right_widget_changed = qtc.pyqtSignal(qtw.QWidget)
    tool_widget_changed = qtc.pyqtSignal(qtw.QWidget)
    samples_changed = qtc.pyqtSignal(list, Sample)
    position_changed = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller: AnnotationBaseClass = None
        self.change_mode(AnnotationMode.MANUAL)

    # SLOTS
    @qtc.pyqtSlot(AnnotationMode)
    def change_mode(self, mode: AnnotationMode) -> None:
        """
        Change the annotation mode.

        Args:
            mode: The new annotation mode.
        """
        assert mode in list(AnnotationMode), "Invalid annotation mode."

        prev_controller = self.controller
        # only change if the selected mode differs from the current mode
        if prev_controller is None or mode != prev_controller.mode:
            if mode == AnnotationMode.MANUAL:
                self.stop_loop.emit()
                self.controller = ManualAnnotation()
            elif mode == AnnotationMode.RETRIEVAL:
                self.controller = RetrievalAnnotation()
            else:
                raise ValueError

            self.controller.start_loop.connect(self.start_loop)
            self.controller.stop_loop.connect(self.stop_loop)
            self.controller.samples_changed.connect(self.samples_changed)
            self.controller.position_changed.connect(self.position_changed)
            self.controller.pause_replay.connect(self.pause_replay)
            self.tool_widget_changed.emit(self.controller.tool_widget)
            self.right_widget_changed.emit(self.controller.main_widget)

            if prev_controller:
                # grab previous state
                samples = prev_controller.samples
                scheme = prev_controller.scheme
                dependencies = prev_controller.dependencies
                n_frames = prev_controller.n_frames
                pos = prev_controller.position

                # disconnect
                prev_controller.disconnect()

                # load controller in place
                self.controller.load(samples, scheme, dependencies, n_frames)
                self.controller.setPosition(pos)

    # ALl below slots need to be forwarded
    @qtc.pyqtSlot(list, AnnotationScheme, np.ndarray, int)
    def load(
        self,
        samples: List[Sample],
        scheme: AnnotationScheme,
        dependencies: np.ndarray,
        n_frames: int,
    ) -> None:
        """
        Load the annotation controller with the given data.

        Args:
            samples: The samples to annotate.
            scheme: The annotation scheme.
            dependencies: The dependencies between the samples.
            n_frames: The number of frames in the video/mocap.
        """
        assert isinstance(samples, list)
        assert isinstance(scheme, AnnotationScheme)
        assert isinstance(dependencies, np.ndarray) or dependencies is None
        assert isinstance(n_frames, int) and n_frames >= 0
        if self.controller:
            self.controller.load(samples, scheme, dependencies, n_frames)

    @qtc.pyqtSlot(int)
    def setPosition(self, x: int) -> None:
        """
        Set the current position of the annotation controller.

        Args:
            x: The new position.
        """
        self.controller.setPosition(x)

    @qtc.pyqtSlot(int)
    def set_position(self, x: int) -> None:
        """
        Set the current position of the annotation controller.

        Args:
            x: The new position.
        """
        self.setPosition(x)

    @qtc.pyqtSlot(bool)
    def setEnabled(self, x: bool) -> None:
        """
        Set the enabled state of the annotation controller.

        Args:
            x: The new enabled state.
        """
        self.controller.setEnabled(x)

    @qtc.pyqtSlot()
    def clear_undo_redo(self) -> None:
        """
        Clear the undo/redo stack.
        """
        self.controller.clear_undo_redo()

    @qtc.pyqtSlot(Sample)
    def insert_sample(self, sample: Sample) -> None:
        """
        Insert a sample.

        Args:
            sample: The sample to insert.
        """
        self.controller.insert_sample(sample)

    @qtc.pyqtSlot(enum.Enum)
    def on_user_action(self, action: AnnotationActions) -> None:
        """
        Handle user actions.

        Args:
            action: The user action.
        """
        self.controller.on_user_action(action)
