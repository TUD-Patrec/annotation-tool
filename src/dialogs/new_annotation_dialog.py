import os

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.data_model import Dataset
from src.data_model.globalstate import GlobalState
from src.media.media_types import get_reader
from src.qt_helper_widgets.line_edit_adapted import QLineEditAdapted
from src.settings import settings


class QNewAnnotationDialog(qtw.QDialog):
    load_annotation = qtc.pyqtSignal(GlobalState)

    def __init__(self, *args, **kwargs):
        super(QNewAnnotationDialog, self).__init__(*args, **kwargs)

        form = qtw.QFormLayout()
        self.annotation_name = qtw.QLineEdit()
        self.annotation_name.setPlaceholderText("Insert name here.")
        self.annotation_name.textChanged.connect(lambda _: self.check_enabled())
        form.addRow("Annotation name:", self.annotation_name)

        self.combobox = qtw.QComboBox()
        for data_description in self.datasets:
            self.combobox.addItem(data_description.name)

        self.combobox.currentIndexChanged.connect(lambda _: self.check_enabled())

        form.addRow("Datasets:", self.combobox)

        self.line_edit = QLineEditAdapted()
        self.line_edit.setPlaceholderText("No File selected.")
        self.line_edit.setReadOnly(True)
        self.line_edit.textChanged.connect(lambda _: self.check_enabled())
        self.line_edit.mousePressed.connect(lambda: self.select_input_source())

        form.addRow("Input File:", self.line_edit)

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

    def select_input_source(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            directory="", filter="Video MoCap (*.mp4 *.avi *.csv)"
        )
        self.line_edit.setText(filename)

    def check_enabled(self):
        enabled = True
        if self.annotation_name.text() == "":
            enabled = False
        if self.combobox.count() == 0:
            enabled = False
        if not (os.path.isfile(self.line_edit.text())):
            enabled = False
        self.open_button.setEnabled(enabled)

    def cancel_pressed(self):
        self.close()

    def open_pressed(self):
        self.check_enabled()
        if self.open_button.isEnabled():
            try:
                media_reader = get_reader(self.line_edit.text())
                if len(media_reader) < 1000:
                    msg = qtw.QMessageBox(self)
                    msg.setIcon(qtw.QMessageBox.Critical)
                    msg.setText("Media too short.")
                    msg.setInformativeText(
                        "The selected media's length [={}] is too small.\nIt should at least consist of 1000 frames!".format(
                            len(media_reader)
                        )
                    )
                    msg.setWindowTitle("Error")
                    msg.exec_()
                    self.line_edit.setText("")
                    self.check_enabled()
                    return
            except ValueError:
                msg = qtw.QMessageBox(self)
                msg.setIcon(qtw.QMessageBox.Critical)
                msg.setText("Unknown media type.")
                msg.setInformativeText("The selected media type is not supported.")
                msg.setWindowTitle("Error")
                msg.exec_()
                self.line_edit.setText("")
                self.check_enabled()
                return

            idx = self.combobox.currentIndex()

            dataset = self.datasets[idx]

            annotator_id = settings.annotator_id
            annotation = GlobalState(
                annotator_id,
                dataset,
                self.annotation_name.text(),
                media_reader,
            )
            self.close()
            self.load_annotation.emit(annotation)

    @property
    def datasets(self):
        return Dataset.get_all()
