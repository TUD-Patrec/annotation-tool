from functools import partial
import logging

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import numpy as np

from src.data_model import Dataset
from src.data_model.annotation_scheme import create_annotation_scheme
from src.qt_helper_widgets.adaptive_scroll_area import QAdaptiveScrollArea
from src.qt_helper_widgets.line_edit_adapted import QLineEditAdapted
from src.utility import filehandler


class QEditDatasets(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vbox = qtw.QVBoxLayout()

        self.scroll_widget = QAdaptiveScrollArea(self)
        self.scroll_widget.setSizePolicy(
            qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding
        )

        vbox.addWidget(self.make_header())
        vbox.addWidget(self.scroll_widget, stretch=1)

        self.bottom_widget = qtw.QWidget()
        self.bottom_widget.setLayout(qtw.QFormLayout())

        self._name = qtw.QLineEdit()
        self._name.setPlaceholderText("No Name")
        self.bottom_widget.layout().addRow("Name:", self._name)

        self._scheme = QLineEditAdapted()
        self._scheme.setPlaceholderText("Path to dataset scheme.")
        self._scheme.setReadOnly(True)
        self._scheme.mousePressed.connect(self.get_scheme_path)
        self.bottom_widget.layout().addRow("Scheme:", self._scheme)

        self._dependencies = QLineEditAdapted()
        self._dependencies.setPlaceholderText("Path to dataset dependencies.")
        self._dependencies.setReadOnly(True)
        self._dependencies.mousePressed.connect(self.get_dependencies_path)
        self.bottom_widget.layout().addRow("Dependencies:", self._dependencies)

        self.add_button = qtw.QPushButton("Add")
        self.add_button.setFixedWidth(100)
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(lambda _: self.add_pressed())
        self.bottom_widget.layout().addRow(self.add_button)

        vbox.addWidget(self.bottom_widget)

        self.setLayout(vbox)
        self.setMinimumSize(600, 400)

        self._reload()

    def get_scheme_path(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(directory="", filter="(*.json)")
        if filehandler.is_non_zero_file(file_path):
            # TODO check scheme valid

            self.add_button.setEnabled(True)
            self._scheme.setText(file_path)
        else:
            self.add_button.setEnabled(False)
            self._scheme.setText("")

    def get_dependencies_path(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(directory="", filter="(*.csv)")
        if filehandler.is_non_zero_file(file_path):
            # TODO check dependencies valid
            self._dependencies.setText(file_path)
        else:
            self._dependencies.setText("")

    def make_header(self):
        row_widget = qtw.QWidget(self)
        hbox = qtw.QHBoxLayout(row_widget)
        row_widget.setLayout(hbox)

        id_lbl = qtw.QLabel("ID")
        id_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(id_lbl)

        name_lbl = qtw.QLabel("Name")
        name_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(name_lbl)

        dependencies_lbl = qtw.QLabel("Dependencies")
        dependencies_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(dependencies_lbl)

        remove_lbl = qtw.QLabel("Remove")
        remove_lbl.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(remove_lbl)

        return row_widget

    def _make_row(self, id):
        row_widget = qtw.QWidget(self)
        hbox = qtw.QHBoxLayout(row_widget)

        dataset = Dataset.get_all()[id]

        idx_label = qtw.QLabel(str(id + 1))
        idx_label.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(idx_label)

        name_label = qtw.QLabel(dataset.name)
        name_label.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(name_label)

        dependencies_exist = (
            "loaded" if dataset.dependencies is not None else "not loaded"
        )
        dependencies_label = qtw.QLabel(dependencies_exist)
        dependencies_label.setAlignment(qtc.Qt.AlignCenter)
        hbox.addWidget(dependencies_label)

        remove_btn = qtw.QPushButton()
        remove_btn.setText("Remove")
        rem_partial = partial(self.remove_pressed, id)
        remove_btn.clicked.connect(lambda _: rem_partial())
        hbox.addWidget(remove_btn)

        row_widget.setLayout(hbox)

        return row_widget

    def _reload(self):
        self.scroll_widget.clear()

        for idx, _ in enumerate(Dataset.get_all()):
            row = self._make_row(idx)
            row.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
            self.scroll_widget.addItem(row)

    def add_pressed(self):
        name = self._name.text()
        if name == "":
            name = "nameless"

        scheme = filehandler.read_json(self._scheme.text())
        try:
            scheme = create_annotation_scheme(scheme)
        except ValueError:
            logging.error(f"{scheme}")
            self._scheme.setText("Could not load scheme.")
            return

        dependency_error_str = "Could not load dependencies."
        dependency_txt = self._dependencies.text()

        dependencies = None

        if len(dependency_txt) > 0:
            if dependency_txt != dependency_error_str:
                try:
                    dependencies = filehandler.read_csv(
                        self._dependencies.text(), data_type=np.int8
                    )
                except FileNotFoundError:
                    self._dependencies.setText(dependency_error_str)
                    return
                if dependencies.shape[0] < 0 or dependencies.shape[1] != len(scheme):
                    self._dependencies.setText(dependency_error_str)
                    return

        Dataset(name, scheme, dependencies)

        self._reload()

        self._name.setText("")
        self._scheme.setText("")
        self._dependencies.setText("")
        self.add_button.setEnabled(False)

    def remove_pressed(self, idx):
        dataset = Dataset.get_all()[idx]
        dataset_name = dataset.name

        msg = qtw.QMessageBox(self)
        msg.setIcon(qtw.QMessageBox.Question)
        msg.setText('Are you sure you want to delete "{}"?'.format(dataset_name))

        msg.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No)
        msg.buttonClicked.connect(lambda x: self.msgbtn(x, dataset))

        msg.show()

    def msgbtn(self, answer, x):
        if answer.text().lower().endswith("yes"):
            x.delete()
            self._reload()
