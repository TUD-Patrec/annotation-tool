import numpy as np
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.annotation.annotation_base import AnnotationBaseClass
from src.annotation.manual.controller import ManualAnnotation
from src.annotation.modes import AnnotationMode
from src.annotation.retrieval.controller import RetrievalAnnotation
from src.data_classes import AnnotationScheme, Sample


class AnnotationController(qtc.QObject):
    start_loop = qtc.pyqtSignal(int, int)
    stop_loop = qtc.pyqtSignal()
    right_widget_changed = qtc.pyqtSignal(qtw.QWidget)
    tool_widget_changed = qtc.pyqtSignal(qtw.QWidget)
    samples_changed = qtc.pyqtSignal(list, Sample)

    def __init__(self, *args, **kwargs):
        super(AnnotationController, self).__init__(*args, **kwargs)
        self.controller: AnnotationBaseClass = None
        self.change_mode(AnnotationMode.MANUAL)

    # SLOTS
    @qtc.pyqtSlot(AnnotationMode)
    def change_mode(self, mode):
        assert mode in [m for m in AnnotationMode]

        prev_controller = self.controller
        # only change if the selected mode differs from the current mode
        if prev_controller is None or mode != prev_controller.mode:
            # grab current values

            if prev_controller:
                samples = prev_controller.samples
                scheme = prev_controller.scheme
                dependencies = prev_controller.dependencies
                n_frames = prev_controller.n_frames

                # disconnect
                prev_controller.disconnect()

            if mode == AnnotationMode.MANUAL:
                self.stop_loop.emit()
                manual_annotation = ManualAnnotation()
                if prev_controller:
                    manual_annotation.load(samples, scheme, dependencies, n_frames)
                self.controller = manual_annotation

            if mode == AnnotationMode.RETRIEVAL:
                retrieval_annotation = RetrievalAnnotation()
                retrieval_annotation = ManualAnnotation()  # TODO REMOVE
                if prev_controller:
                    retrieval_annotation.load(samples, scheme, dependencies, n_frames)
                self.controller = retrieval_annotation

            # Connect Signals and Slots
            self.controller.start_loop.connect(self.start_loop)
            self.controller.stop_loop.connect(self.stop_loop)
            self.controller.samples_changed.connect(self.samples_changed)

            # Emit new widgets
            self.tool_widget_changed.emit(self.controller.tool_widget)
            self.right_widget_changed.emit(self.controller.main_widget)

    # ALl below slots need to be forwarded
    @qtc.pyqtSlot(list, AnnotationScheme, np.ndarray, int)
    def load(self, samples, scheme, dependencies, n_frames):
        assert isinstance(samples, list)
        assert isinstance(scheme, AnnotationScheme)
        assert isinstance(dependencies, np.ndarray) or dependencies is None
        assert isinstance(n_frames, int) and n_frames >= 0
        if self.controller:
            self.controller.load(samples, scheme, dependencies, n_frames)

    @qtc.pyqtSlot(int)
    def setPosition(self, x):
        self.controller.setPosition(x)

    @qtc.pyqtSlot(int)
    def set_position(self, x):
        self.setPosition(x)

    @qtc.pyqtSlot(bool)
    def setEnabled(self, x):
        self.controller.setEnabled(x)

    @qtc.pyqtSlot()
    def undo(self):
        self.controller.undo()

    @qtc.pyqtSlot()
    def redo(self):
        self.controller.redo()

    @qtc.pyqtSlot()
    def clear_undo_redo(self):
        self.controller.clear_undo_redo()

    @qtc.pyqtSlot()
    def annotate(self):
        self.controller.annotate()

    @qtc.pyqtSlot()
    def cut(self):
        self.controller.cut()

    @qtc.pyqtSlot()
    def cut_and_annotate(self):
        self.controller.cut_and_annotate()

    @qtc.pyqtSlot(bool)
    def merge(self, left):
        self.controller.merge(left)

    @qtc.pyqtSlot(Sample)
    def insert_sample(self, sample):
        self.controller.insert_sample(sample)
