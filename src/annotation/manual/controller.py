from copy import deepcopy

from src.annotation.annotation_base import AnnotationBaseClass
from src.annotation.manual.main_widget import QDisplaySample
from src.annotation.manual.tool_widget import ManualAnnotationTools
from src.annotation.modes import AnnotationMode
from src.data_model import Sample
from src.dialogs.annotation_dialog import QAnnotationDialog


class ManualAnnotation(AnnotationBaseClass):
    def __init__(self):
        super().__init__()

        self.mode = AnnotationMode.MANUAL

        self.main_widget = QDisplaySample()

        self.tool_widget = ManualAnnotationTools()
        self.tool_widget.annotate.connect(self.annotate)
        self.tool_widget.cut.connect(self.cut)
        self.tool_widget.cut_and_annotate.connect(self.cut_and_annotate)
        self.tool_widget.merge.connect(self.merge)

        self.samples_changed.connect(self.main_widget.setSelected)

    def add_to_undo_stack(self):
        current_samples = deepcopy(self.samples)

        self.redo_stack = []  # clearing redo_stack
        self.undo_stack.append(current_samples)

        while len(self.undo_stack) > self.MAX_UNDO_STACK_SIZE:
            self.undo_stack.pop(0)

    def load_subclass(self):
        # Nothing to add here
        self.setEnabled(True)

    def redo(self):
        if len(self.redo_stack) >= 1:
            current_samples = deepcopy(self.samples)
            self.undo_stack.append(current_samples)

            self.samples = self.redo_stack.pop()
            self.check_for_selected_sample(force_update=True)

    def undo(self):
        if len(self.undo_stack) >= 1:
            current_samples = deepcopy(self.samples)
            self.redo_stack.append(current_samples)

            self.samples = self.undo_stack.pop()
            self.check_for_selected_sample(force_update=True)

    def annotate(self):
        if self.enabled:
            dialog = QAnnotationDialog(
                self.selected_sample, self.scheme, self.dependencies
            )
            dialog.finished.connect(lambda _: self.check_for_selected_sample(True))
            self.open_dialog(dialog)

    def cut(self):
        if self.enabled:
            sample = self.selected_sample

            # Split can only happen if you are at least at second frame of that sample
            if sample.start_position < self.position:
                start_1, end_1 = sample.start_position, self.position
                start_2, end_2 = self.position + 1, sample.end_position

                s1 = Sample(start_1, end_1, sample.annotation)
                s2 = Sample(start_2, end_2, deepcopy(sample.annotation))

                assert s1.annotation is not s2.annotation

                self.add_to_undo_stack()

                idx = self.samples.index(sample)
                self.samples.remove(sample)
                self.samples.insert(idx, s1)
                self.samples.insert(idx + 1, s2)

                self.check_for_selected_sample()

    def cut_and_annotate(self):
        if self.enabled:
            self.cut()
            self.annotate()

    def merge(self, left):
        if self.enabled:
            sample = self.selected_sample

            sample_idx = self.samples.index(sample)

            other_idx = sample_idx - 1 if left else sample_idx + 1
            if 0 <= other_idx < len(self.samples):
                other_sample = self.samples[other_idx]
                start = min(sample.start_position, other_sample.start_position)
                end = max(sample.end_position, other_sample.end_position)

                merged_sample = Sample(start, end, sample.annotation)

                self.add_to_undo_stack()

                self.samples.remove(sample)
                self.samples.remove(other_sample)
                self.samples.insert(min(sample_idx, other_idx), merged_sample)

                self.check_for_selected_sample()

    def insert_sample(self, new_sample):
        pass
