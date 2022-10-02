import logging
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from copy import deepcopy
from src.data_classes.globalstate import GlobalState
from src.data_classes.sample import Sample
from src.dialogs.annotation_dialog import QAnnotationDialog
from src.annotation.timeline import QTimeLine


class QAnnotationWidget(qtw.QWidget):
    samples_changed = qtc.pyqtSignal(list, Sample)

    def __init__(self, *args, **kwargs):
        super(QAnnotationWidget, self).__init__(*args, **kwargs)
        self.global_state = None
        self.position = 0
        self.selected_sample = None

        self.undo_stack = list()
        self.redo_stack = list()

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

    @qtc.pyqtSlot(int)
    def set_position(self, new_pos):
        assert 0 <= new_pos, f"{new_pos = }"
        assert (
            self.n_frames == 0 or new_pos < self.n_frames
        ), f"{new_pos = }, {self.n_frames = }"
        if new_pos != self.position:
            self.position = new_pos
            self.check_for_selected_sample()

    @qtc.pyqtSlot(GlobalState)
    def load_state(self, state):
        assert isinstance(state, GlobalState)
        self.clear_undo_redo()
        self.global_state = state
        self.position = 0
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
        self.split_selected_sample()
        self.annotate_selected_sample()

    @qtc.pyqtSlot()
    def annotate_selected_sample(self):
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

    @qtc.pyqtSlot(Sample)
    def new_sample(self, new_sample):
        logging.info(f"RECEIVED NEW SAMPLE {new_sample}")
        assert len(self.samples) > 0

        left = -1  # index to the rightmost sample with: new_sample.lower >= left.lower
        right = -1  # index to the leftmost sample with: new_sample.upper <= right.lower

        for idx, s in enumerate(self.samples):
            if s.start_position <= new_sample.start_position <= s.end_position:
                left = idx
            if s.start_position <= new_sample.end_position <= s.end_position:
                right = idx
            if s.start_position > new_sample.end_position:
                break

        # Case 1: upper != lower
        # if left != right:
        if 1:
            logging.info("CASE 1")
            logging.info(f"{left = }, {right = }")
            tmp = [self.samples[idx] for idx in range(left, right + 1)]
            logging.info(f"{len(tmp) = }")

            N_old = len(self.samples)
            for s in tmp:
                self.samples.remove(s)
            assert N_old == len(self.samples) + len(tmp)

            left_sample = Sample(
                tmp[0].start_position,
                new_sample.start_position - 1,
                deepcopy(tmp[0].annotation),
            )
            if left_sample.end_position > left_sample.start_position:
                self.samples.append(left_sample)

            if new_sample.start_position < new_sample.end_position:
                self.samples.append(new_sample)

            right_sample = Sample(
                new_sample.end_position + 1,
                tmp[-1].end_position,
                deepcopy(tmp[-1].annotation),
            )
            if right_sample.end_position > right_sample.start_position:
                self.samples.append(right_sample)

        # Case 2: upper == lower -> x is completely within one sample
        else:
            logging.info("CASE 2")
            # Split needed -> 3 new samples -> check if all have len > 0
            outer_sample = self.samples[left]
            logging.info(f"{outer_sample = }, {left = }, {right = }")

            N_before = len(self.samples)
            self.samples.remove(outer_sample)
            logging.info(f"check_remove: {N_before = } {len(self.samples) = }")

            new_left_sample = Sample(
                outer_sample.start_position,
                new_sample.start_position - 1,
                deepcopy(outer_sample.annotation),
            )
            if new_left_sample.start_position < new_left_sample.end_position:
                self.samples.append(new_left_sample)
                logging.info(f"{new_left_sample = }")

            self.samples.append(new_sample)
            logging.info(f"{new_sample = }")

            new_right_sample = Sample(
                new_sample.end_position + 1,
                outer_sample.end_position,
                deepcopy(outer_sample.annotation),
            )
            if new_right_sample.start_position < new_right_sample.end_position:
                self.samples.append(new_right_sample)
                logging.info(f"{new_right_sample = }")

        self.samples.sort()
        self.check_for_selected_sample(force_update=True)

    @property
    def samples(self):
        return self.global_state.samples if self.global_state is not None else []

    @samples.setter
    def samples(self, new_samples):
        assert isinstance(new_samples, list)
        for s in new_samples:
            assert isinstance(s, Sample)
        self.global_state.samples = new_samples

    @property
    def n_frames(self):
        return self.global_state.n_frames if self.global_state is not None else 0

    @property
    def scheme(self):
        return self.global_state.dataset.scheme

    @property
    def dependencies(self):
        return self.global_state.dataset.dependencies
