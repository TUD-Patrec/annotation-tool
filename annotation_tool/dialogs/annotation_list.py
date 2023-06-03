import os
from pathlib import Path
import shutil

import PyQt6.QtCore as qtc
from PyQt6.QtGui import QIntValidator
import PyQt6.QtWidgets as qtw

from annotation_tool.data_model.annotation import Annotation
from annotation_tool.utility import filehandler


class AnnotationManagerWidget(qtw.QWidget):
    deleted = qtc.pyqtSignal()

    def __init__(self, global_state: Annotation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_annotation = global_state
        self.init_ui()
        self._delete = False

    def init_ui(self):
        self.grid = qtw.QGridLayout(self)

        # name
        self.name_label = qtw.QLabel("Name")
        self.name_edit = qtw.QLineEdit(self.current_annotation.name)
        self.name_edit.textChanged.connect(self.name_changed)
        self.grid.addWidget(self.name_label, 0, 0)
        self.grid.addWidget(self.name_edit, 0, 1)

        # file
        self.file_label = qtw.QLabel("File")
        file_name = os.path.basename(self.current_annotation.path)
        self.file_edit = qtw.QLineEdit(file_name)
        self.file_edit.setReadOnly(True)
        self.file_edit.setToolTip(self.current_annotation.path.as_posix())
        self.grid.addWidget(self.file_label, 1, 0)
        self.grid.addWidget(self.file_edit, 1, 1)

        # annotator id
        self.annotator_id_label = qtw.QLabel("Annotator ID")
        self.annotator_id_edit = qtw.QLineEdit(
            str(self.current_annotation.annotator_id)
        )
        onlyInt = QIntValidator()
        onlyInt.setRange(0, 1000)
        self.annotator_id_edit.setValidator(onlyInt)
        self.annotator_id_edit.setMaxLength(3)
        self.annotator_id_edit.textChanged.connect(self.annotator_id_changed)
        self.grid.addWidget(self.annotator_id_label, 2, 0)
        self.grid.addWidget(self.annotator_id_edit, 2, 1)

        # timestamp
        self.timestamp_label = qtw.QLabel("Created")
        self.timestamp_edit = qtw.QLineEdit(self.current_annotation.timestamp)
        self.timestamp_edit.setReadOnly(True)
        self.grid.addWidget(self.timestamp_label, 3, 0)
        self.grid.addWidget(self.timestamp_edit, 3, 1)

        # dataset
        self.dataset_label = qtw.QLabel("Dataset")
        self.dataset_edit = qtw.QLineEdit(self.current_annotation.dataset.name)
        self.dataset_edit.setReadOnly(True)
        self.grid.addWidget(self.dataset_label, 4, 0)
        self.grid.addWidget(self.dataset_edit, 4, 1)

        # show progress as a colored bar
        self.progress_label = qtw.QLabel("Progress")
        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.current_annotation.progress)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.grid.addWidget(self.progress_label, 5, 0)
        self.grid.addWidget(self.progress_bar, 5, 1)

        # Export button and Delete button in a horizontal layout
        self.button_layout = qtw.QHBoxLayout()
        self.export_button = qtw.QPushButton("Export")
        self.export_button.clicked.connect(self.export)
        self.button_layout.addWidget(self.export_button)
        self.delete_button = qtw.QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete)
        self.button_layout.addWidget(self.delete_button)
        self.grid.addLayout(self.button_layout, 6, 0, 1, 2)

        # set layout
        self.setLayout(self.grid)

        # use minimal height
        height = self.minimumSizeHint().height()
        self.setFixedHeight(height)

    def name_changed(self):
        self.current_annotation.name = self.name_edit.text()

    def annotator_id_changed(self):
        if self.annotator_id_edit.text() != "":
            self.current_annotation.annotator_id = int(self.annotator_id_edit.text())

    def export(self):
        # open export dialog
        dlg = ExportAnnotationDialog(self.current_annotation, self)
        dlg.exec()
        dlg.deleteLater()

    def delete(self):
        # ask for confirmation
        msg = qtw.QMessageBox(self)
        msg.setIcon(qtw.QMessageBox.Icon.Warning)
        msg.setText("Do you really want to delete this Annotation-Object?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setWindowTitle("Delete Annotation-Object")
        msg.setStandardButtons(
            qtw.QMessageBox.StandardButton.Yes | qtw.QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(qtw.QMessageBox.StandardButton.No)
        if msg.exec() == qtw.QMessageBox.StandardButton.Yes:
            self.current_annotation.delete()
            self.deleted.emit()


class GlobalStateList(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # make scrollable
        self.scroll = qtw.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = qtw.QWidget()
        self.scroll.setWidget(self.scroll_content)
        self.scroll_layout = qtw.QVBoxLayout(self.scroll_content)

        # add layout
        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.scroll)

        self.update()

    def update(self) -> None:
        # clear layout
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        # add global states
        annotations = Annotation.get_all()
        for annotation in annotations:
            widget = AnnotationManagerWidget(annotation)
            widget.deleted.connect(self.update)

            # make frame around the widget
            frame = qtw.QFrame()
            frame.setFrameShape(qtw.QFrame.Shape.StyledPanel)
            frame.setFrameShadow(qtw.QFrame.Shadow.Raised)
            frame_layout = qtw.QVBoxLayout(frame)
            frame_layout.addWidget(widget)
            frame.setFixedHeight(widget.size().height())

            self.scroll_layout.addWidget(frame)


class GlobalStatesDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Annotations")
        self.setMinimumSize(500, 500)
        self.grid = qtw.QGridLayout(self)

        self.scroll_global_states = GlobalStateList()
        self.grid.addWidget(self.scroll_global_states)

    def update(self):
        self.scroll_global_states.update()


class ExportAnnotationDialog(qtw.QDialog):
    def __init__(self, annotation: Annotation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_annotation = annotation
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Export Annotation {}".format(self.current_annotation.name))
        self.setMinimumSize(500, 500)
        self.grid = qtw.QGridLayout(self)

        # Give the user some options and group them visual box with a title
        self.export_options = qtw.QGroupBox("Export Options")
        self.export_options_layout = qtw.QGridLayout(self.export_options)

        # Option 1) Add copy of annotated file
        self.add_copy_label = qtw.QLabel("Copy of annotated file:")
        self.add_copy_checkbox = qtw.QCheckBox()
        self.add_copy_checkbox.setChecked(False)
        self.export_options_layout.addWidget(self.add_copy_label, 0, 0)
        self.export_options_layout.addWidget(self.add_copy_checkbox, 0, 1)

        # Option 2) Export dataset-scheme
        self.export_dataset_scheme_label = qtw.QLabel("Dataset scheme:")
        self.export_dataset_scheme_checkbox = qtw.QCheckBox()
        self.export_dataset_scheme_checkbox.setChecked(False)
        self.export_options_layout.addWidget(self.export_dataset_scheme_label, 1, 0)
        self.export_options_layout.addWidget(self.export_dataset_scheme_checkbox, 1, 1)

        # Option 3) Export meta informations
        self.export_meta_informations_label = qtw.QLabel("Meta informations:")
        self.export_meta_informations_checkbox = qtw.QCheckBox()
        self.export_meta_informations_checkbox.setChecked(False)
        self.export_options_layout.addWidget(self.export_meta_informations_label, 2, 0)
        self.export_options_layout.addWidget(
            self.export_meta_informations_checkbox, 2, 1
        )

        # Option 4) Compress everything into a zip file
        self.compress_label = qtw.QLabel("Compress to zip:")
        self.compress_checkbox = qtw.QCheckBox()
        self.compress_checkbox.setChecked(True)
        self.export_options_layout.addWidget(self.compress_label, 3, 0)
        self.export_options_layout.addWidget(self.compress_checkbox, 3, 1)

        # Export Buttond and Cancel Button
        self.button_box = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.StandardButton.Ok
            | qtw.QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Add all widgets to the grid
        self.grid.addWidget(self.export_options, 0, 0)
        self.grid.addWidget(self.button_box, 1, 0)

    def accept(self):
        # ask for export path
        export_path = qtw.QFileDialog.getExistingDirectory(self, "Select Directory")
        if not export_path:
            return

        # annotation name
        annotation_name = "annotation_{}_by_{}".format(
            self.current_annotation.name, self.current_annotation.annotator_id
        )

        # create export directory
        export_dir = os.path.join(export_path, annotation_name)
        os.makedirs(export_dir, exist_ok=True)

        # Export main annotation-file
        array = self.current_annotation.to_numpy()
        scheme = self.current_annotation.dataset.scheme
        header = [x.element_name for x in scheme]
        filehandler.write_csv(
            Path(os.path.join(export_dir, "annotation.csv")), array, header
        )

        # add copy of annotated file
        if self.add_copy_checkbox.isChecked():
            shutil.copy2(self.current_annotation.path, export_dir)

        # export dataset-scheme
        if self.export_dataset_scheme_checkbox.isChecked():
            filehandler.write_json(
                Path(os.path.join(export_dir, "dataset_scheme.json")),
                self.current_annotation.dataset.scheme.scheme,
            )

        # export meta informations
        if self.export_meta_informations_checkbox.isChecked():
            filehandler.write_json(
                Path(os.path.join(export_dir, "meta_informations.json")),
                self.current_annotation.meta_data,
            )

        # compress to zip file
        if self.compress_checkbox.isChecked():
            shutil.make_archive(export_dir, "zip", export_dir)
            shutil.rmtree(export_dir)

        super().accept()

    def reject(self):
        super().reject()
