import logging
import os
import shutil

import PyQt5.QtWidgets as qtw
import numpy as np

from ..qt_helper_widgets.line_edit_adapted import QLineEditAdapted
from ..utility import filehandler, functions


class QExportAnnotationDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super(QExportAnnotationDialog, self).__init__(*args, **kwargs)
        form = qtw.QFormLayout()
        self.annotation_combobox = qtw.QComboBox()

        self.annotations = functions.get_annotations()
        for annotation in self.annotations:
            self.annotation_combobox.addItem(annotation.name)

        self.annotation_combobox.currentIndexChanged.connect(
            lambda _: self.check_enabled()
        )
        form.addRow("Annotation Name:", self.annotation_combobox)

        self.naming_combobox = qtw.QComboBox()
        self.naming_combobox.addItem("default")

        self.export_path_line_edit = QLineEditAdapted()
        self.export_path_line_edit.setPlaceholderText("No Directory selected.")
        self.export_path_line_edit.setReadOnly(True)
        self.export_path_line_edit.mousePressed.connect(self.get_path)
        self.export_path_line_edit.textChanged.connect(lambda _: self.check_enabled())
        form.addRow("Export Directory:", self.export_path_line_edit)

        self.export_annotated_file = qtw.QCheckBox()
        form.addRow("Add Copy of annotated File:", self.export_annotated_file)

        self.export_scheme = qtw.QCheckBox()
        form.addRow("Add dataset-scheme:", self.export_scheme)

        self.export_dependencies = qtw.QCheckBox()
        form.addRow("Add dataset-dependencies:", self.export_dependencies)

        self.export_meta_informations = qtw.QCheckBox()
        form.addRow("Add meta-informations:", self.export_meta_informations)

        self.zip_exportation = qtw.QCheckBox()
        form.addRow("Compress files into ZIP-archive:", self.zip_exportation)

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
        self.setMinimumWidth(400)

    def get_path(self):
        path = qtw.QFileDialog.getExistingDirectory(self, directory="")
        if os.path.isdir(path):
            self.export_path_line_edit.setText(path)

    def check_enabled(self):
        enabled = True

        idx = self.annotation_combobox.currentIndex()
        if idx == -1:
            enabled = False

        if not (os.path.isdir(self.export_path_line_edit.text())):
            enabled = False

        self.open_button.setEnabled(enabled)

    def cancel_pressed(self):
        self.close()

    def open_pressed(self):
        dir_path = self.export_path_line_edit.text()
        idx = self.annotation_combobox.currentIndex()

        # Grab informations from annotation.pkl
        annotation = self.annotations[idx]
        annotated_file = annotation.input_file
        input_filename = os.path.split(annotated_file)[1]
        annotator_id = annotation.annotator_id

        # Create directory for exportation
        folder = os.path.join(
            dir_path, "annotation_{}_by_{}".format(annotation.name, annotator_id)
        )
        if os.path.isdir(folder):
            logging.warning("ALREADY EXISTING: {}".format(folder))
        exportation_directory = filehandler.create_dir(folder)
        del folder

        # Export main annotation-file
        array = annotation.load_mocap()
        filehandler.write_csv(
            os.path.join(exportation_directory, "annotation.csv"), array
        )
        logging.info("{} created.".format("annotation.csv"))

        # Export copy of the annotated file
        if self.export_annotated_file.isChecked():
            out_path = os.path.join(exportation_directory, input_filename)
            logging.info("Copying {} -> {}".format(annotated_file, out_path))
            shutil.copy2(annotated_file, out_path)
            logging.info("Copying succesfull.")
            del out_path

        # Export dataset-scheme
        if self.export_scheme.isChecked():
            logging.info("Exporting dataset-scheme.")
            out_path = os.path.join(exportation_directory, "scheme.json")
            annotation_scheme = annotation.dataset.scheme
            filehandler.write_json(data=annotation_scheme.scheme, path=out_path)
            del out_path

        # Export dataset-dependencies
        if self.export_dependencies.isChecked():
            logging.info("Exporting dataset-dependencies.")
            out_path = os.path.join(exportation_directory, "dependencies.csv")
            data = np.array(annotation.dataset.dependencies)
            filehandler.write_csv(path=out_path, data=data)
            del out_path
            del data

        # Export meta-informations
        if self.export_meta_informations.isChecked():
            logging.info("Exporting meta-informations")
            meta_dict = dict()
            meta_dict["name"] = annotation.name
            meta_dict["dataset_name"] = annotation.dataset.name
            meta_dict["annotator_id"] = annotation.annotator_id
            meta_dict["input_file"] = annotation.input_file
            meta_dict["footprint"] = annotation.footprint

            out_path = os.path.join(exportation_directory, "meta_informations.json")
            filehandler.write_json(path=out_path, data=meta_dict)
            del meta_dict
            del out_path

        # Compress Folder to ZIP
        if self.zip_exportation.isChecked():
            logging.info("CREATING ZIP-Archive.")
            out_path = os.path.join(
                dir_path, "annotation_{}_by_{}".format(annotation.name, annotator_id)
            )
            shutil.make_archive(out_path, "zip", exportation_directory)
            shutil.rmtree(exportation_directory)
            logging.info("ZIP-File created.")

        self.close()
