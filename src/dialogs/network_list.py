import os

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.data_model import Model, get_unique_name, make_model
from src.media import MediaType


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
        file_dialog.setFileMode(qtw.QFileDialog.ExistingFile)
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
        msg_box = qtw.QMessageBox()
        msg_box.setText("Do you really want to delete this network?")
        msg_box.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No)
        msg_box.setDefaultButton(qtw.QMessageBox.No)
        if msg_box.exec() == qtw.QMessageBox.Yes:
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
            frame.setFrameShape(qtw.QFrame.StyledPanel)
            frame.setFrameShadow(qtw.QFrame.Raised)
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

        # media type - combo box
        self.media_type_label = qtw.QLabel("Media Type:")
        self.media_type_edit = qtw.QComboBox()
        for media_type in MediaType:
            self.media_type_edit.addItem(media_type.name)
        self.layout.addWidget(self.media_type_label)
        self.layout.addWidget(self.media_type_edit)

        # buttons
        self.button_box = qtw.QDialogButtonBox(
            qtw.QDialogButtonBox.Ok | qtw.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # disable ok button
        self.button_box.button(qtw.QDialogButtonBox.Ok).setEnabled(False)

        self.setLayout(self.layout)

    def on_path_clicked(self, event: qtg.QMouseEvent):
        file_dialog = qtw.QFileDialog(self)
        file_dialog.setFileMode(qtw.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Network (*.pt *.pth)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.path_edit.setText(file_path)

            # enable ok button
            self.button_box.button(qtw.QDialogButtonBox.Ok).setEnabled(True)

    def get_name(self) -> str:
        return self.name_edit.text()

    def get_path(self) -> str:
        return self.path_edit.text()

    def get_sampling_rate(self) -> int:
        return self.sampling_rate_edit.value()

    def get_media_type(self) -> MediaType:
        return MediaType[self.media_type_edit.currentText()]


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
        create_dialog = CreateNetworkDialog()
        if create_dialog.exec():
            name = create_dialog.get_name()
            path = create_dialog.get_path()
            sampling_rate = create_dialog.get_sampling_rate()
            media_type = create_dialog.get_media_type()
            make_model(path, sampling_rate, media_type, name)
            self.update()


# make test application with dialog
if __name__ == "__main__":
    import sys

    app = qtw.QApplication(sys.argv)
    dialog = NetworksDialog()
    dialog.show()
    app.exec_()
