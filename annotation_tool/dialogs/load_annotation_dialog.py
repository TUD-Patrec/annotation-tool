import os

import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw

from ..data_model import Dataset
from ..data_model.annotation import Annotation
from ..qt_helper_widgets.line_edit_adapted import QLineEditAdapted
from ..utility import filehandler


class LoadAnnotationDialog(qtw.QDialog):
    load_annotation = qtc.pyqtSignal(Annotation)

    def __init__(self, *args, **kwargs):
        super(LoadAnnotationDialog, self).__init__(*args, **kwargs)

        self.global_states = Annotation.get_all()
        self.global_states.sort(key=lambda x: x.timestamp, reverse=True)

        self.name_changed_msg = (
            "The name of the annotation has changed, please insert the new name."
        )
        self.path_changed_msg = (
            "The path of the annotation has changed, please select the new file."
        )

        self.init_ui()

        self.process_combobox_value(0)

    def init_ui(self):
        self.setWindowTitle("Load Annotation")
        self.setModal(True)

        form = qtw.QFormLayout()
        self.combobox = qtw.QComboBox()

        for global_state in self.global_states:
            self.combobox.addItem(global_state.name)

        self.combobox.currentIndexChanged.connect(
            lambda x: self.process_combobox_value(x)
        )
        form.addRow("Name:", self.combobox)

        self.line_edit = QLineEditAdapted()
        self.line_edit.setPlaceholderText("No associated input file found.")
        self.line_edit.setReadOnly(True)
        self.line_edit.textChanged.connect(lambda _: self.check_enabled())
        self.line_edit.mousePressed.connect(lambda: self.select_input_source())
        form.addRow("File:", self.line_edit)

        self.dataset_line_edit = qtw.QLineEdit()
        self.dataset_line_edit.setPlaceholderText("No associated dataset found.")
        self.dataset_line_edit.setReadOnly(True)
        form.addRow("Dataset:", self.dataset_line_edit)

        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        form.addRow("Progress:", self.progress_bar)

        self.open_button = qtw.QPushButton()
        self.open_button.setText("Open")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(lambda _: self.open_pressed())

        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(lambda _: self.cancel_pressed())

        self.button_widget = qtw.QWidget()
        self.button_widget.setLayout(qtw.QHBoxLayout())
        self.button_widget.layout().addWidget(self.open_button)
        self.button_widget.layout().addWidget(self.cancel_button)

        form.addRow(self.button_widget)
        self.setLayout(form)
        self.setMinimumWidth(500)

    def process_combobox_value(self, idx):
        if idx >= 0 and idx < len(self.global_states):
            global_state = self.global_states[idx]

            dataset = global_state.dataset

            self.dataset_line_edit.setText(dataset.name)

            if dataset not in self.datasets:
                depr_str = self.dataset_line_edit.text() + " [Deleted]"
                self.dataset_line_edit.setText(depr_str)
                self.dataset_line_edit.setStatusTip(
                    "The original Dataset was deleted via the Edit-Dataset Menu."
                )

            if os.path.isfile(global_state.path):
                self.line_edit.setText(global_state.path)
            else:
                self.line_edit.setText(
                    "The path of the input has changed, please select the new path."
                )

            self.progress_bar.setValue(global_state.progress)

        self.check_enabled()

    def select_input_source(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(
            parent=self, directory="", filter="Video MoCap (*.mp4 *.avi *.csv)"
        )
        if filehandler.is_non_zero_file(file_path):
            hash = filehandler.footprint_of_file(file_path)
            idx = self.combobox.currentIndex()

            if idx < 0:
                self.line_edit.setText("")
                return

            global_state: Annotation = self.global_states[idx]
            other_hash = global_state.footprint

            if hash == other_hash:
                self.line_edit.setText(file_path)
            else:
                self.line_edit.setText(
                    "The input_file is not compatible with the selected global_state, please select the correct file."  # noqa E501
                )
        self.check_enabled()

    def check_enabled(self):
        if self.combobox.count() == 0:
            self.open_button.setEnabled(False)
        elif not (os.path.isfile(self.line_edit.text())):
            self.open_button.setEnabled(False)
        elif self.combobox.currentIndex() < 0:
            self.open_button.setEnabled(False)
        else:
            self.open_button.setEnabled(True)

    def cancel_pressed(self):
        self.close()

    def open_pressed(self):
        idx = self.combobox.currentIndex()
        global_state = self.global_states[idx]
        path = self.line_edit.text()
        file_hash = filehandler.footprint_of_file(path)

        if file_hash == global_state.footprint:
            global_state.path = self.line_edit.text()
            self.close()
            self.load_annotation.emit(global_state)
        else:
            self.line_edit.setText(
                "The input_file is not compatible with the selected global_state, please select the correct file."  # noqa E501
            )

    @property
    def datasets(self):
        return Dataset.get_all()
