import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from copy import deepcopy
from src.data_classes.sample import Sample
from src.dialogs.annotation_dialog import QAnnotationDialog


class QAnnotationWidget(qtw.QWidget):
    samples_changed = qtc.pyqtSignal(list, Sample)

    def __init__(self, *args, **kwargs):
        super(QAnnotationWidget, self).__init__(*args, **kwargs)
        self.samples = []
        self.scheme = None
        self.dependencies = None
        self.position = 0
        self.n_frames = 0
        self.selected_sample = None

        self.undo_stack = list()
        self.redo_stack = list()

        self.enabled = False

        self.init_UI()

    def init_UI(self):
        self.annotate_btn = qtw.QPushButton("Annotate", self)
        self.annotate_btn.setStatusTip(
            "Open the Annotation-Dialog for the highlighted sample."
        )
        self.annotate_btn.clicked.connect(lambda _: self.annotate_selected_sample())

        self.cut_btn = qtw.QPushButton("Cut", self)
        self.cut_btn.setStatusTip("Split the highlighted sample into two pieces.")
        self.cut_btn.clicked.connect(lambda _: self.split_selected_sample())

        self.cut_and_annotate_btn = qtw.QPushButton("C+A", self)
        self.cut_and_annotate_btn.setStatusTip(
            "Cut and immediately annotate the current sample."
        )
        self.cut_and_annotate_btn.clicked.connect(lambda _: self.cut_and_annotate())

        self.merge_left_btn = qtw.QPushButton("Merge Left", self)
        self.merge_left_btn.setStatusTip(
            "Merge highlighted sample with the left neighbour."
        )
        self.merge_left_btn.clicked.connect(
            lambda _: self.merge_samples(merge_left=True)
        )

        self.merge_right_btn = qtw.QPushButton("Merge Right", self)
        self.merge_right_btn.setStatusTip(
            "Merge highlighted sample with the right neighbour"
        )
        self.merge_right_btn.clicked.connect(
            lambda _: self.merge_samples(merge_left=False)
        )

        # layout
        vbox = qtw.QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)

        vbox.addWidget(self.annotate_btn)
        vbox.addWidget(self.cut_btn)
        vbox.addWidget(self.cut_and_annotate_btn)
        vbox.addWidget(self.merge_left_btn)
        vbox.addWidget(self.merge_right_btn)

        self.setLayout(vbox)

    @qtc.pyqtSlot(bool)
    def setEnabled(self, a0: bool) -> None:
        self.enabled = bool(a0)
        self.annotate_btn.setEnabled(self.enabled)
        self.cut_btn.setEnabled(self.enabled)
        self.cut_and_annotate_btn.setEnabled(self.enabled)
        self.merge_left_btn.setEnabled(self.enabled)
        self.merge_right_btn.setEnabled(self.enabled)

    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        assert 0 <= new_pos, f"{new_pos = }"
        assert (
            self.n_frames == 0 or new_pos < self.n_frames
        ), f"{new_pos = }, {self.n_frames = }"
        if new_pos != self.position:
            self.position = new_pos
            self.check_for_selected_sample()

    @qtc.pyqtSlot(list, int)
    def load(self, samples, scheme, dependencies, n_frames):
        self.samples = samples
        self.scheme = scheme
        self.dependencies = dependencies
        self.n_frames = n_frames
        self.position = 0
        self.clear_undo_redo()
        self.check_for_selected_sample(force_update=True)

    # TODO maybe use binary search to increase speed, currently O(n)
    @qtc.pyqtSlot(int)
    def check_for_selected_sample(self, force_update=False):
        for s in self.samples:
            if s.start_position <= self.position <= s.end_position:
                sample = s
                break
        else:
            raise RuntimeError("Could not find sample")
        if force_update or self.selected_sample is not sample:
            self.selected_sample = sample
            self.samples_changed.emit(self.samples, sample)

    @qtc.pyqtSlot()
    def cut_and_annotate(self):
        if self.is_enabled():
            self.split_selected_sample()
            self.annotate_selected_sample()

    @qtc.pyqtSlot()
    def annotate_selected_sample(self):
        if self.is_enabled():
            sample = self.selected_sample

            dialog = QAnnotationDialog(self.scheme, self.dependencies)

            dialog.new_annotation.connect(
                lambda x: self.update_sample_annotation(sample, x)
            )
            dialog.open()
            dialog._set_annotation(sample.annotation)

    def update_sample_annotation(self, sample, new_annotation):
        self.add_to_undo_stack()
        sample.annotation = new_annotation
        self.samples_changed.emit(self.samples, self.selected_sample)

    @qtc.pyqtSlot()
    def split_selected_sample(self):
        if self.is_enabled():
            sample = self.selected_sample

            # Split can only happen if you are at least at second frame of that sample
            if sample.start_position < self.position:
                start_1, end_1 = sample.start_position, self.position
                start_2, end_2 = self.position + 1, sample.end_position

                s1 = Sample(start_1, end_1, sample.annotation)
                s2 = Sample(start_2, end_2, sample.annotation)

                self.add_to_undo_stack()

                idx = self.samples.index(sample)
                self.samples.remove(sample)
                self.samples.insert(idx, s1)
                self.samples.insert(idx + 1, s2)

                self.check_for_selected_sample()

    @qtc.pyqtSlot(bool)
    def merge_samples(self, merge_left: bool = None):
        if self.is_enabled():
            sample = self.selected_sample

            sample_idx = self.samples.index(sample)

            other_idx = sample_idx - 1 if merge_left else sample_idx + 1
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

    def add_to_undo_stack(self):
        current_samples = deepcopy(self.samples)

        self.redo_stack = []  # clearing redo_stack
        self.undo_stack.append(current_samples)

        while len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if len(self.undo_stack) >= 1:
            current_samples = deepcopy(self.samples)
            self.redo_stack.append(current_samples)

            self.samples = self.undo_stack.pop()
            self.check_for_selected_sample(force_update=True)

    def redo(self):
        if len(self.redo_stack) >= 1:
            current_samples = deepcopy(self.samples)
            self.undo_stack.append(current_samples)

            self.samples = self.redo_stack.pop()
            self.check_for_selected_sample(force_update=True)

    def clear_undo_redo(self):
        self.undo_stack = []
        self.redo_stack = []

    def is_enabled(self):
        return self.enabled and bool(self.samples)

    @qtc.pyqtSlot(Sample)
    def new_sample(self, new_sample):
        assert len(self.samples) > 0

        left = None  # index to the rightmost sample with: new_sample.lower >= left.lower
        right = None  # index to the leftmost sample with: new_sample.upper <= right.lower

        # grab those indices
        for idx, s in enumerate(self.samples):
            if s.start_position <= new_sample.start_position <= s.end_position:
                left = idx
            if s.start_position <= new_sample.end_position <= s.end_position:
                right = idx
            if s.start_position > new_sample.end_position:
                break

        # must not be the case
        assert left is not None and right is not None

        # grab all samples that share some common frame-positions with the new sample
        tmp = [self.samples[idx] for idx in range(left, right + 1)]

        # remove all of them from the sample-list
        for s in tmp:
            self.samples.remove(s)

        # create new left_sample
        left_sample = Sample(
            tmp[0].start_position,
            new_sample.start_position - 1,
            deepcopy(tmp[0].annotation),
        )

        # only add it if it is valid
        if left_sample.start_position <= left_sample.end_position:
            self.samples.append(left_sample)

        # create new right sample
        right_sample = Sample(
            new_sample.end_position + 1,
            tmp[-1].end_position,
            deepcopy(tmp[-1].annotation),
        )

        # only add it if it is valid
        if right_sample.start_position <= right_sample.end_position:
            self.samples.append(right_sample)

        # add new sample if it is valid
        if new_sample.start_position <= new_sample.end_position:
            self.samples.append(new_sample)

        # reorder samples -> the <= 3 newly added samples were appended to the end
        self.samples.sort()

        # merge neighbors with same annotation -> left_neighbor must not be the same as left_sample previously,
        # same for right neighbor
        idx = self.samples.index(new_sample)
        # only if the new sample is not the first list element
        if idx > 0:
            left_neighbor = self.samples[idx - 1]
            if left_neighbor.annotation == new_sample.annotation:
                self.samples.remove(left_neighbor)
                new_sample.start_position = left_neighbor.start_position
        # only if the new sample is not the last list element
        if idx < len(self.samples) - 1:
            right_neighbor = self.samples[idx + 1]
            if right_neighbor.annotation == new_sample.annotation:
                self.samples.remove(right_neighbor)
                new_sample.end_position = right_neighbor.end_position

        # update samples and notify timeline etc.
        self.check_for_selected_sample(force_update=True)

