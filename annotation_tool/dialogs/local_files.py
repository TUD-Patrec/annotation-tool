import math
import os
import platform
import subprocess

import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw

from annotation_tool.file_cache._file_cache import (
    get_all,
    get_dir,
    get_size_in_bytes,
    path_of,
)
from annotation_tool.qt_helper_widgets.lines import QHLine


class LocalFilesDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Local Files")
        self.setLayout(qtw.QGridLayout(self))

        # layout - spread second column
        self.layout().setColumnStretch(1, 1)

        # create list widget
        self.list_widget = qtw.QListWidget()
        self.populate_list_widget()
        self.layout().addWidget(self.list_widget, 0, 0, 1, 2)

        # show total number of files
        self.num_files_label = qtw.QLabel("Number of stored objects:")
        self.num_files_label_value = qtw.QLabel(f"{len(get_all())}")
        self.layout().addWidget(self.num_files_label, 1, 0)
        self.layout().addWidget(self.num_files_label_value, 1, 1)

        # show total size of directory
        self.size_label = qtw.QLabel("Total Size on disk:")
        self.size_label_value = qtw.QLabel(
            f" {math.ceil(get_size_in_bytes() / 1024)} KB"
        )
        self.layout().addWidget(self.size_label, 2, 0)
        self.layout().addWidget(self.size_label_value, 2, 1)

        # show directory path and button to copy it
        self.path_label = qtw.QLabel("Path to local files:")
        self.path_value_label = qtw.QLabel(f"{get_dir()}")
        self.path_value_label.setWordWrap(True)
        self.path_value_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.layout().addWidget(self.path_label, 3, 0)
        self.layout().addWidget(self.path_value_label, 3, 1)

        # make button box with copy path and open dir buttons
        self.copy_path_button = qtw.QPushButton("Copy Path")
        self.copy_path_button.clicked.connect(self.copy_path)
        self.open_dir_button = qtw.QPushButton("Open in Explorer")
        self.open_dir_button.clicked.connect(self.open_dir)

        # add buttons to own layout and add layout to dialog
        self.button_box_layout = qtw.QHBoxLayout()
        self.button_box_layout.addWidget(self.copy_path_button)
        self.button_box_layout.addWidget(self.open_dir_button)
        self.layout().addLayout(self.button_box_layout, 4, 0, 1, 2)

        # add horizontal line
        self.layout().addWidget(QHLine(), 5, 0, 1, 2)

        # add close button
        self.close_button = qtw.QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.layout().addWidget(self.close_button, 6, 0, 1, 2)

    def copy_path(self):
        qtw.QApplication.clipboard().setText(get_dir())

    def open_dir(self):
        path = get_dir()
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def accept(self):
        super().accept()

    def populate_list_widget(self):
        for cached_object in get_all():
            class_name = cached_object.__class__.__name__

            _path = path_of(cached_object)
            _size_in_bytes = os.path.getsize(_path)
            _size_in_kb = math.ceil(_size_in_bytes / 1024)
            _encoded_id = os.path.basename(_path)

            item = qtw.QListWidgetItem()
            item.setText(f"{_encoded_id} - {class_name} - {_size_in_kb} KB")
            self.list_widget.addItem(item)
