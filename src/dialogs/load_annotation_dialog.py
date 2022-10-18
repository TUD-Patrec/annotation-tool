import os

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from ..dataclasses.globalstate import GlobalState
from ..qt_helper_widgets.line_edit_adapted import QLineEditAdapted
from ..utility import filehandler, functions


class QLoadExistingAnnotationDialog(qtw.QDialog):
    load_annotation = qtc.pyqtSignal(GlobalState)

    def __init__(self, *args, **kwargs):
        super(QLoadExistingAnnotationDialog, self).__init__(*args, **kwargs)
        form = qtw.QFormLayout()
        self.combobox = qtw.QComboBox()

        self.annotations = functions.get_annotations()
        for annotation in self.annotations:
            self.combobox.addItem(annotation.name)

        self.combobox.currentIndexChanged.connect(
            lambda x: self.process_combobox_value(x)
        )

        form.addRow("Annotation_Name:", self.combobox)

        self.line_edit = QLineEditAdapted()
        self.line_edit.setPlaceholderText("No associated Input-File found.")
        self.line_edit.setReadOnly(True)
        self.line_edit.textChanged.connect(lambda _: self.check_enabled())
        self.line_edit.mousePressed.connect(lambda: self.select_input_source())

        form.addRow("Input File:", self.line_edit)

        self.dataset_line_edit = qtw.QLineEdit()
        self.dataset_line_edit.setPlaceholderText("No associated Dataset found.")
        self.dataset_line_edit.setReadOnly(True)

        form.addRow("Dataset Path:", self.dataset_line_edit)

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

        self.process_combobox_value(self.combobox.currentIndex())

    def process_combobox_value(self, idx):
        if idx >= 0:
            annotation = self.annotations[idx]

            dataset = annotation.dataset

            self.dataset_line_edit.setText(dataset.name)

            if not filehandler.is_non_zero_file(dataset.path):
                depr_str = self.dataset_line_edit.text() + " [Deleted]"
                self.dataset_line_edit.setText(depr_str)
                self.dataset_line_edit.setStatusTip(
                    "The original Dataset was deleted via the Edit-Dataset Menu."
                )

            if os.path.isfile(annotation.input_file):
                hash = filehandler.footprint_of_file(annotation.input_file)
                if annotation.footprint == hash:
                    self.line_edit.setText(annotation.input_file)
                else:
                    self.line_edit.setText(
                        "The path of the input has changed, please select the new path."
                    )
            else:
                self.line_edit.setText(
                    "The path of the input has changed, please select the new path."
                )
        self.check_enabled()

    def select_input_source(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(
            directory="", filter="Video MoCap (*.mp4 *.avi *.csv)"
        )
        if filehandler.is_non_zero_file(file_path):
            hash = filehandler.footprint_of_file(file_path)
            idx = self.combobox.currentIndex()

            if idx < 0:
                self.line_edit.setText("")
                return

            annotation = self.annotations[idx]
            other_hash = annotation.footprint

            if hash == other_hash:
                self.line_edit.setText(file_path)
            else:
                self.line_edit.setText(
                    "The input_file is not compatible with the selected annotation, please select the correct file."  # noqa E501
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
        annotation = self.annotations[idx]

        annotation.input_file = self.line_edit.text()

        self.load_annotation.emit(annotation)
        self.close()
