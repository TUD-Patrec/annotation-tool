import os

import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw
import numpy as np

from annotation_tool.data_model import Annotation, Dataset, create_global_state
from annotation_tool.media_reader import media_reader as mr
from annotation_tool.qt_helper_widgets.line_edit_adapted import QLineEditAdapted
from annotation_tool.settings import settings


class ImportAnnotationDialog(qtw.QDialog):
    load_annotation = qtc.pyqtSignal(Annotation)

    def __init__(self, *args, **kwargs):
        super(ImportAnnotationDialog, self).__init__(*args, **kwargs)

        self.input_path = None
        self.annotation_path = None
        self.annotation_name = None
        self.dataset = None

        self._file_error_msg = "Please select a valid file."
        self._name_error_msg = "Please insert a valid name."
        self._dataset_error_msg = "Please select a valid dataset."

        # UI components
        self.combobox = None
        self.input_path_edit = None
        self.annotation_name_edit = None
        self.open_button = None
        self.cancel_button = None
        self.button_widget = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Import Annotation")
        self.setMinimumWidth(500)
        self.setModal(True)

        form = qtw.QFormLayout(self)

        self.annotation_path_edit = QLineEditAdapted()
        self.annotation_path_edit.setPlaceholderText("No File selected.")
        self.annotation_path_edit.setReadOnly(True)
        self.annotation_path_edit.mousePressed.connect(self.select_annotation_source)
        form.addRow("Annotation:", self.annotation_path_edit)

        self.input_path_edit = QLineEditAdapted()
        self.input_path_edit.setPlaceholderText("No File selected.")
        self.input_path_edit.setReadOnly(True)
        self.input_path_edit.textChanged.connect(self.path_changed)
        self.input_path_edit.mousePressed.connect(self.select_input_source)
        form.addRow("File:", self.input_path_edit)

        self.annotation_name_edit = qtw.QLineEdit()
        self.annotation_name_edit.setPlaceholderText("")
        self.annotation_name_edit.textChanged.connect(self.name_changed)
        form.addRow("Name:", self.annotation_name_edit)

        self.combobox = qtw.QComboBox()
        for data_description in self._datasets:
            self.combobox.addItem(data_description.name)
        self.combobox.currentIndexChanged.connect(self.dataset_changed)
        form.addRow("Dataset:", self.combobox)

        self.open_button = qtw.QPushButton()
        self.open_button.setText("Create")
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

        self.dataset_changed(self.combobox.currentIndex())  # initialize dataset

    @qtc.pyqtSlot(str)
    def path_changed(self, txt):
        if os.path.isfile(txt):
            self.input_path = txt
            base_name = os.path.basename(txt)  # get filename
            base_name = os.path.splitext(base_name)[0]  # remove extension

            # check if annotation with same name already exists
            if base_name in self._annotation_names:
                idx = 1
                tmp_name = f"{base_name} [{idx}]"
                while tmp_name in self._annotation_names:
                    tmp_name = f"{base_name} [{idx}]"
                    idx += 1
                base_name = tmp_name

            self.annotation_name_edit.setText(base_name)
        else:
            self.input_path = None
            self.input_path_edit.setText("")
            self.input_path_edit.setPlaceholderText(self._file_error_msg)

        self.check_enabled()

    @qtc.pyqtSlot(str)
    def name_changed(self, txt):
        if txt != "":
            self.annotation_name = txt
        else:
            self.annotation_name = None
            self.annotation_name_edit.setText("")
            self.annotation_name_edit.setPlaceholderText(self._name_error_msg)

        self.check_enabled()

    def dataset_changed(self, idx):
        if idx >= 0:
            self.dataset = self._datasets[idx]
        else:
            self.dataset = None
        self.check_enabled()

    def select_annotation_source(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            parent=self, directory="", filter="Video MoCap (*.csv)"
        )
        self.annotation_path_edit.setText(filename)
        self.annotation_path = filename

    def select_input_source(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            parent=self, directory="", filter="Video MoCap (*.mp4 *.avi *.csv)"
        )
        self.input_path_edit.setText(filename)

    def check_enabled(self):
        enabled = (
            self.annotation_path is not None
            and self.input_path is not None
            and self.annotation_name is not None
            and self.dataset is not None
        )
        self.open_button.setEnabled(enabled)

    def cancel_pressed(self):
        self.close()

    def open_pressed(self):
        self.check_enabled()
        if self.open_button.isEnabled():
            from ..data_model import create_annotation, create_sample
            from ..utility.filehandler import read_csv

            try:
                annotation = read_csv(self.annotation_path)
            except ValueError:
                msg = qtw.QMessageBox(self)
                msg.setIcon(qtw.QMessageBox.Icon.Critical)
                msg.setText("Unknown annotation type.")
                msg.setInformativeText(
                    "The selected annotation file is not a valid annotation file."
                )
                msg.setWindowTitle("Error")
                msg.exec()
                self.annotation_path_edit.setText("")
                self.annotation_path_edit.setPlaceholderText(self._file_error_msg)
                self.annotation_path = None
                self.check_enabled()
                return
            except FileNotFoundError:
                msg = qtw.QMessageBox(self)
                msg.setIcon(qtw.QMessageBox.Icon.Critical)
                msg.setText("Annotation file not found.")
                msg.setInformativeText(
                    "The selected annotation file could not be found."
                )
                msg.setWindowTitle("Error")
                msg.exec()
                self.annotation_path_edit.setText("")
                self.annotation_path_edit.setPlaceholderText(self._file_error_msg)
                self.annotation_path = None
                self.check_enabled()
                return

            try:
                media_reader = mr(self.input_path)
            except ValueError:
                msg = qtw.QMessageBox(self)
                msg.setIcon(qtw.QMessageBox.Icon.Critical)
                msg.setText("Unknown media type.")
                msg.setInformativeText("The selected media type is not supported.")
                msg.setWindowTitle("Error")
                msg.exec()
                self.input_path_edit.setText("")
                self.input_path_edit.setPlaceholderText(self._file_error_msg)
                self.input_path = None
                self.check_enabled()
                return

            if len(annotation.shape) != 2:
                msg = qtw.QMessageBox(self)
                msg.setIcon(qtw.QMessageBox.Icon.Critical)
                msg.setText("Invalid annotation file.")
                msg.setInformativeText(
                    "The selected annotation file is not a valid annotation file."
                )
                msg.setWindowTitle("Error")
                msg.exec()
                self.annotation_path_edit.setText("")
                self.annotation_path_edit.setPlaceholderText(self._file_error_msg)
                self.annotation_path = None
                self.check_enabled()
                return

            if annotation.shape[0] != len(media_reader):
                msg = qtw.QMessageBox(self)
                msg.setIcon(qtw.QMessageBox.Icon.Critical)
                msg.setText("Annotation and media file do not match.")
                msg.setInformativeText(
                    "The selected annotation file does not match the selected media file."
                )
                msg.setWindowTitle("Error")
                msg.exec()
                self.annotation_path_edit.setText("")
                self.annotation_path_edit.setPlaceholderText(self._file_error_msg)
                self.annotation_path = None
                self.check_enabled()
                return

            idx = self.combobox.currentIndex()
            dataset = self._datasets[idx]
            scheme = dataset.scheme

            samples = []
            start_idx = 0
            for idx in range(annotation.shape[0]):
                if idx == annotation.shape[0] - 1 or not np.array_equal(
                    annotation[idx], annotation[idx + 1]
                ):
                    try:
                        _anno = create_annotation(scheme, annotation[idx])
                    except ValueError:
                        msg = qtw.QMessageBox(self)
                        msg.setIcon(qtw.QMessageBox.Icon.Critical)
                        msg.setText("Invalid annotation.")
                        msg.setInformativeText(
                            "The selected annotation file contains invalid annotations."
                        )
                        msg.setWindowTitle("Error")
                        msg.exec()
                        self.annotation_path_edit.setText("")
                        self.annotation_path_edit.setPlaceholderText(
                            self._file_error_msg
                        )
                        self.annotation_path = None
                        self.check_enabled()
                        return

                    samples.append(create_sample(start_idx, idx, _anno))
                    start_idx = idx + 1

            annotator_id = settings.annotator_id
            annotation = create_global_state(
                annotator_id,
                dataset,
                self.annotation_name_edit.text(),
                media_reader.path,
            )

            annotation.samples = samples

            self.close()
            self.load_annotation.emit(annotation)

    @property
    def _datasets(self):
        return Dataset.get_all()

    @property
    def _annotation_names(self):
        return [a.name for a in Annotation.get_all()]
