import os
import shutil

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.data_model.globalstate import GlobalState
from src.utility import filehandler


class GlobalStateWidget(qtw.QWidget):
    deleted = qtc.pyqtSignal()

    def __init__(self, global_state: GlobalState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.global_state = global_state
        self.init_ui()

    def init_ui(self):
        self.grid = qtw.QGridLayout(self)

        # name
        self.name_label = qtw.QLabel("Name")
        self.name_edit = qtw.QLineEdit(self.global_state.name)
        self.name_edit.textChanged.connect(self.name_changed)
        self.grid.addWidget(self.name_label, 0, 0)
        self.grid.addWidget(self.name_edit, 0, 1)

        # file
        self.file_label = qtw.QLabel("File")
        file_name = os.path.basename(self.global_state.media.path)
        self.file_edit = qtw.QLineEdit(file_name)
        self.file_edit.setReadOnly(True)
        self.file_edit.setToolTip(self.global_state.media.path)
        self.grid.addWidget(self.file_label, 1, 0)
        self.grid.addWidget(self.file_edit, 1, 1)

        # annotator id
        self.annotator_id_label = qtw.QLabel("Annotator ID")
        self.annotator_id_edit = qtw.QLineEdit(str(self.global_state.annotator_id))
        self.annotator_id_edit.textChanged.connect(self.annotator_id_changed)
        self.grid.addWidget(self.annotator_id_label, 2, 0)
        self.grid.addWidget(self.annotator_id_edit, 2, 1)

        # timestamp
        self.timestamp_label = qtw.QLabel("Timestamp")
        self.timestamp_edit = qtw.QLineEdit(self.global_state.timestamp)
        self.timestamp_edit.setReadOnly(True)
        self.grid.addWidget(self.timestamp_label, 3, 0)
        self.grid.addWidget(self.timestamp_edit, 3, 1)

        # dataset
        self.dataset_label = qtw.QLabel("Dataset")
        self.dataset_edit = qtw.QLineEdit(self.global_state.dataset.name)
        self.dataset_edit.setReadOnly(True)
        self.grid.addWidget(self.dataset_label, 4, 0)
        self.grid.addWidget(self.dataset_edit, 4, 1)

        # show progress as a colored bar
        self.progress_label = qtw.QLabel("Progress")
        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.global_state.progress)
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

    def name_changed(self):
        self.global_state.name = self.name_edit.text()

    def annotator_id_changed(self):
        self.global_state.annotator_id = self.annotator_id_edit.text()

    def export(self):
        # open export dialog
        self.exp_dialog = ExportAnnotationDialog(self.global_state)
        self.exp_dialog.exec_()
        self.exp_dialog.deleteLater()

    def delete(self):
        # ask for confirmation
        msg = qtw.QMessageBox()
        msg.setIcon(qtw.QMessageBox.Warning)
        msg.setText("Do you really want to delete this Annotation-Object?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setWindowTitle("Delete Annotation-Object")
        msg.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No)
        msg.setDefaultButton(qtw.QMessageBox.No)
        msg.buttonClicked.connect(self.delete_confirmation)
        msg.exec_()

    def delete_confirmation(self, button):
        # check if yes in button text
        if "yes" in button.text().lower():
            self.global_state.delete()
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
        global_states = GlobalState.get_all()
        # global_states.sort(key=lambda x: x.creation_time, reverse=True)
        for global_state in global_states:
            widget = GlobalStateWidget(global_state)
            widget.deleted.connect(self.update)

            # make frame around the widget
            frame = qtw.QFrame()
            frame.setFrameShape(qtw.QFrame.StyledPanel)
            frame.setFrameShadow(qtw.QFrame.Raised)
            frame_layout = qtw.QVBoxLayout(frame)
            frame_layout.addWidget(widget)

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

        self.button_box = qtw.QDialogButtonBox(qtw.QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.grid.addWidget(self.button_box)

    def update(self):
        self.scroll_global_states.update()


class ExportAnnotationDialog(qtw.QDialog):
    def __init__(self, global_state: GlobalState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.global_state = global_state
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Export Annotation {}".format(self.global_state.name))
        self.setMinimumSize(500, 500)
        self.grid = qtw.QGridLayout(self)

        # Give the user some options and group them visual box with a title
        self.export_options = qtw.QGroupBox("Export Options")
        self.export_options_layout = qtw.QGridLayout(self.export_options)

        # Option 1) Add copy of annotated file
        self.add_copy_label = qtw.QLabel("Add copy of annotated file:")
        self.add_copy_checkbox = qtw.QCheckBox()
        self.add_copy_checkbox.setChecked(False)
        self.export_options_layout.addWidget(self.add_copy_label, 0, 0)
        self.export_options_layout.addWidget(self.add_copy_checkbox, 0, 1)

        # Option 2) Export dataset-scheme
        self.export_dataset_scheme_label = qtw.QLabel("Export dataset-scheme:")
        self.export_dataset_scheme_checkbox = qtw.QCheckBox()
        self.export_dataset_scheme_checkbox.setChecked(False)
        self.export_options_layout.addWidget(self.export_dataset_scheme_label, 1, 0)
        self.export_options_layout.addWidget(self.export_dataset_scheme_checkbox, 1, 1)

        # Option 3) Export meta informations
        self.export_meta_informations_label = qtw.QLabel("Export meta informations:")
        self.export_meta_informations_checkbox = qtw.QCheckBox()
        self.export_meta_informations_checkbox.setChecked(False)
        self.export_options_layout.addWidget(self.export_meta_informations_label, 2, 0)
        self.export_options_layout.addWidget(
            self.export_meta_informations_checkbox, 2, 1
        )

        # Option 4) Compress everything into a zip file
        self.compress_label = qtw.QLabel("Compress everything into a zip file:")
        self.compress_checkbox = qtw.QCheckBox()
        self.compress_checkbox.setChecked(True)
        self.export_options_layout.addWidget(self.compress_label, 3, 0)
        self.export_options_layout.addWidget(self.compress_checkbox, 3, 1)

        # Export Buttond and Cancel Button
        self.button_box = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.Ok | qtw.QDialogButtonBox.Cancel
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
            self.global_state.name, self.global_state.annotator_id
        )

        # create export directory
        export_dir = os.path.join(export_path, annotation_name)
        os.makedirs(export_dir, exist_ok=True)

        # Export main annotation-file
        array = self.global_state.to_numpy()
        scheme = self.global_state.dataset.scheme
        header = [x.element_name for x in scheme]
        filehandler.write_csv(os.path.join(export_dir, "annotation.csv"), array, header)

        # add copy of annotated file
        if self.add_copy_checkbox.isChecked():
            shutil.copy2(self.global_state.media.path, export_dir)

        # export dataset-scheme
        if self.export_dataset_scheme_checkbox.isChecked():
            filehandler.write_json(
                os.path.join(export_dir, "dataset_scheme.json"),
                self.global_state.dataset.scheme.scheme,
            )

        # export meta informations
        if self.export_meta_informations_checkbox.isChecked():
            filehandler.write_json(
                os.path.join(export_dir, "meta_informations.json"),
                self.global_state.meta_data,
            )

        # compress to zip file
        if self.compress_checkbox.isChecked():
            shutil.make_archive(export_dir, "zip", export_dir)
            shutil.rmtree(export_dir)

        super().accept()

    def reject(self):
        super().reject()
