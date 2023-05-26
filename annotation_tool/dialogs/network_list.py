import os
import re

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.data_model import Model, create_model, get_unique_name
from annotation_tool.data_model.media_type import MediaType


def parse_input_shape(input_str: str):
    """
    Parse a string in the form of "(x, y, z)" or "((x_min, x_max), (y_min, *), (z_min, z_max))" to a tuple of ints.
    """
    _magical_number = 78173827

    # Remove all spaces and parentheses and split by comma
    shapes = input_str
    shapes = shapes.replace(" ", "")

    # basic regex
    pos_number = r"[1-9]\d*"
    min_max_tuple = r"\({},{}\)|\({},\*\)".format(*([pos_number] * 3))

    # Check if the string is empty
    if not shapes:
        raise ValueError("Empty input shape")

    # Check string starts with "(" and ends with ")"
    if not shapes.startswith("(") or not shapes.endswith(")"):
        raise ValueError("Input shape must start with '(' and end with ')'")

    # check if the paranthes contain anything
    if len(shapes) == 2:
        raise ValueError("Input shape must contain at least one element")

    # Remove outer parentheses
    shapes = shapes[1:-1]

    tuples = re.findall(min_max_tuple, shapes)  # inner tuples
    placeholder = "_tpl_"
    shapes = re.sub(
        min_max_tuple, placeholder, shapes
    )  # replace inner tuples with _tpl_ for later parsing

    # split by comma
    shapes = shapes.split(",")

    res = []

    print(tuples, shapes)

    for shape in shapes:
        if shape == placeholder:
            inner_tuple = tuples.pop(0)
            min_, max_ = inner_tuple.replace("(", "").replace(")", "").split(",")
            min_ = int(min_)
            max_ = int(max_) if max_ != "*" else _magical_number
            if min_ > max_:
                raise ValueError(
                    f"The first value must be smaller the second one, got {min_} and {max_}"
                )
            if min_ <= 0 or max_ <= 0:
                raise ValueError(f"Values must be positive, got {min_} and {max_}")
            res.append((min_, max_))

        else:
            if re.match(pos_number, shape) is None:
                raise ValueError(f"Expected positive integer, got {shape}")
            val = int(shape)
            if val <= 0:
                raise ValueError(f"Value must be positive, got {val}")
            res.append(val)

    return tuple(res)


class NetworkWidget(qtw.QWidget):
    deleted = qtc.pyqtSignal()

    def __init__(self, model: Model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.init_ui()

    def init_ui(self):
        self.grid = qtw.QGridLayout(self)

        # name
        self.name_label = qtw.QLabel("Name:")
        self.name_edit = qtw.QLineEdit(self.model.name)
        self.grid.addWidget(self.name_label, 0, 0)
        self.grid.addWidget(self.name_edit, 0, 1)

        # path to network
        self.path_label = qtw.QLabel("Path:")
        # readonly -> open file dialog on click
        self.path_edit = qtw.QLineEdit(self.model.network_path)
        # make text red if path does not exist
        if not os.path.exists(self.model.network_path):
            self.path_edit.setStyleSheet("color: red")
            self.path_edit.setToolTip("File does not exist.")
        self.path_edit.setReadOnly(True)
        self.path_edit.mousePressEvent = self.on_path_clicked
        self.grid.addWidget(self.path_label, 1, 0)
        self.grid.addWidget(self.path_edit, 1, 1)

        # sampling rate spinbox
        self.sampling_rate_label = qtw.QLabel("Sampling rate:")
        self.sampling_rate_edit = qtw.QSpinBox()
        self.sampling_rate_edit.setRange(1, 1000)
        self.sampling_rate_edit.wheelEvent = lambda event: None
        self.sampling_rate_edit.setValue(self.model.sampling_rate)
        self.grid.addWidget(self.sampling_rate_label, 2, 0)
        self.grid.addWidget(self.sampling_rate_edit, 2, 1)

        # media type dropdown
        self.media_type_label = qtw.QLabel("Media Type:")
        self.media_type_edit = qtw.QComboBox()
        self.media_type_edit.wheelEvent = lambda event: None
        self.media_type_edit.addItems([media_type.name for media_type in MediaType])
        self.media_type_edit.setCurrentText(self.model.media_type.name)
        self.grid.addWidget(self.media_type_label, 5, 0)
        self.grid.addWidget(self.media_type_edit, 5, 1)

        # activated checkbox
        self.activated_label = qtw.QLabel("Activated:")
        self.activated_edit = qtw.QCheckBox()
        self.activated_edit.setChecked(self.model.activated)
        self.grid.addWidget(self.activated_label, 6, 0)
        self.grid.addWidget(self.activated_edit, 6, 1)

        # update and delete buttons, put in separate widget
        self.button_widget = qtw.QWidget()
        self.button_layout = qtw.QHBoxLayout(self.button_widget)
        self.update_button = qtw.QPushButton("Update")
        self.update_button.clicked.connect(self.on_update_clicked)
        self.delete_button = qtw.QPushButton("Delete")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.button_layout.addWidget(self.update_button)
        self.button_layout.addWidget(self.delete_button)
        self.grid.addWidget(self.button_widget, 7, 0, 1, 2)

        # set layout
        self.setLayout(self.grid)

    def on_path_clicked(self, event: qtg.QMouseEvent):
        file_dialog = qtw.QFileDialog(self)
        file_dialog.setFileMode(qtw.QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Network (*.pt *.pth)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.path_edit.setText(file_path)
            # make text red if path does not exist
            if not os.path.exists(file_path):
                self.path_edit.setStyleSheet("color: red")
                self.path_edit.setToolTip("File does not exist.")
            else:
                self.path_edit.setStyleSheet("color: black")
                self.path_edit.setToolTip("")

    def on_delete_clicked(self):
        # ask for confirmation
        msg_box = qtw.QMessageBox(self)
        msg_box.setText("Do you really want to delete this network?")
        msg_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.Yes | qtw.QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
        if msg_box.exec() == qtw.QMessageBox.StandardButton.Yes:
            self.model.delete()
            self.deleted.emit()

    def on_update_clicked(self):
        # update model
        self.model.name = self.name_edit.text()
        self.model.network_path = self.path_edit.text()
        self.model.sampling_rate = self.sampling_rate_edit.value()
        self.model.media_type = MediaType[self.media_type_edit.currentText()]
        self.model.activated = self.activated_edit.isChecked()

        # highlight widget for 1 second to indicate that the model was updated
        self.setStyleSheet("background-color: lightgreen")
        qtc.QTimer.singleShot(1000, lambda: self.setStyleSheet(""))


class NetworkListWidget(qtw.QWidget):
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

    def update(self):
        # clear layout
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        # add networks
        models = Model.get_all()
        for model in models:
            widget = NetworkWidget(model)
            widget.deleted.connect(self.update)

            # make frame around the widget
            frame = qtw.QFrame()
            frame.setFrameShape(qtw.QFrame.Shape.StyledPanel)
            frame.setFrameShadow(qtw.QFrame.Shadow.Raised)
            frame_layout = qtw.QVBoxLayout(frame)
            frame_layout.addWidget(widget)

            self.scroll_layout.addWidget(frame)


class CreateNetworkDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # set title
        self.setWindowTitle("Create Network")

        # set layout
        self.layout = qtw.QVBoxLayout(self)

        # name
        self.name_label = qtw.QLabel("Name:")
        self.name_edit = qtw.QLineEdit()
        default_name = get_unique_name()
        self.name_edit.setText(default_name)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_edit)

        # path to network -> Must be set
        self.path_label = qtw.QLabel("Path to Network:")
        self.path_edit = qtw.QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.mousePressEvent = self.on_path_clicked
        self.layout.addWidget(self.path_label)
        self.layout.addWidget(self.path_edit)

        # sampling rate - int spinner
        self.sampling_rate_label = qtw.QLabel("Sampling Rate:")
        self.sampling_rate_edit = qtw.QSpinBox()
        self.sampling_rate_edit.setRange(1, 1000)
        self.sampling_rate_edit.setValue(100)
        self.layout.addWidget(self.sampling_rate_label)
        self.layout.addWidget(self.sampling_rate_edit)

        self.input_shape_label = qtw.QLabel("Input Shape:")
        self.input_shape_edit = qtw.QLineEdit()
        self.input_shape_edit.setPlaceholderText("e.g. (100, (100, *), 1000)")
        self.input_shape_label.setToolTip(
            "The input shape of the network. Batch-size is not included. Examples: (100, 200), (100, (150, *), 1000), (100, (100, 100), 1000)"
        )

        self.layout.addWidget(self.input_shape_label)
        self.layout.addWidget(self.input_shape_edit)

        # media type - combo box
        self.media_type_label = qtw.QLabel("Media Type:")
        self.media_type_edit = qtw.QComboBox()
        for media_type in MediaType:
            self.media_type_edit.addItem(media_type.name)
        self.layout.addWidget(self.media_type_label)
        self.layout.addWidget(self.media_type_edit)

        # buttons
        self.button_box = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.StandardButton.Ok
            | qtw.QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # disable ok button
        self.button_box.button(qtw.QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.setLayout(self.layout)

    def on_path_clicked(self, event: qtg.QMouseEvent):
        file_dialog = qtw.QFileDialog(self)
        file_dialog.setFileMode(qtw.QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Network (*.pt *.pth)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.path_edit.setText(file_path)

            # enable ok button
            self.button_box.button(qtw.QDialogButtonBox.StandardButton.Ok).setEnabled(
                True
            )

    def get_name(self) -> str:
        return self.name_edit.text()

    def get_path(self) -> str:
        return self.path_edit.text()

    def get_sampling_rate(self) -> int:
        return self.sampling_rate_edit.value()

    def get_media_type(self) -> MediaType:
        return MediaType[self.media_type_edit.currentText()]

    def get_input_shape(self) -> tuple:
        return parse_input_shape(self.input_shape_edit.text())


class NetworksDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # set title
        self.setWindowTitle("Networks")
        self.setMinimumSize(500, 500)

        self.grid = qtw.QGridLayout(self)

        # add network list widget
        self.network_list_widget = NetworkListWidget()
        self.grid.addWidget(self.network_list_widget, 0, 0, 1, 2)

        # add button for creating new network
        self.create_button = qtw.QPushButton("Create")
        self.create_button.clicked.connect(self.on_create_clicked)
        self.grid.addWidget(self.create_button, 1, 0)

        # add button for closing dialog
        self.close_button = qtw.QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.grid.addWidget(self.close_button, 1, 1)

    def update(self):
        self.network_list_widget.update()

    def on_create_clicked(self):
        create_dialog = CreateNetworkDialog(self)
        if create_dialog.exec():
            name = create_dialog.get_name()
            path = create_dialog.get_path()
            sampling_rate = create_dialog.get_sampling_rate()
            media_type = create_dialog.get_media_type()
            input_shape = create_dialog.get_input_shape()
            create_model(
                network_path=path,
                media_type=media_type,
                sampling_rate=sampling_rate,
                input_shape=input_shape,
                name=name,
            )
            self.update()
