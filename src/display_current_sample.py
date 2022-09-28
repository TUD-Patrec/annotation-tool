import logging

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from .qt_helper_widgets.lines import QHLine
from .qt_helper_widgets.display_scheme import QShowAnnotation


class QDisplaySample(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(QDisplaySample, self).__init__(*args, **kwargs)
        self.init_UI()

    def init_UI(self):
        self.top_widget = qtw.QLabel("CURRENT SAMPLE", alignment=qtc.Qt.AlignCenter)

        self.start_label = qtw.QLabel("Start Frame:", alignment=qtc.Qt.AlignCenter)
        self.start_value = qtw.QLabel("A", alignment=qtc.Qt.AlignCenter)
        self.end_label = qtw.QLabel("End Frame:", alignment=qtc.Qt.AlignCenter)
        self.end_value = qtw.QLabel("B", alignment=qtc.Qt.AlignCenter)

        self.middle_widget = QShowAnnotation()

        self.bottom_left_widget = qtw.QWidget()
        self.bottom_left_widget.setLayout(qtw.QFormLayout())
        self.bottom_left_widget.layout().addRow(self.start_label, self.start_value)
        self.bottom_left_widget.layout().addRow(self.end_label, self.end_value)

        self.bottom_right_widget = qtw.QWidget()
        self.bottom_right_widget.setLayout(qtw.QVBoxLayout())

        self.bottom_widget = qtw.QWidget()
        self.bottom_widget.setLayout(qtw.QHBoxLayout())
        self.bottom_widget.layout().addWidget(self.bottom_left_widget)
        self.bottom_widget.layout().addWidget(self.bottom_right_widget)

        vbox = qtw.QVBoxLayout()
        vbox.addWidget(self.top_widget, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.middle_widget, alignment=qtc.Qt.AlignCenter, stretch=1)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.bottom_widget, alignment=qtc.Qt.AlignCenter)

        self.setLayout(vbox)
        self.setMinimumWidth(300)

    def set_selected(self, _, sample):
        if sample is None:
            self.middle_widget.show_annotation(None)
            self.start_value.setText(str(0))
            self.end_value.setText(str(0))
        else:
            self.middle_widget.show_annotation(sample.annotation)
            self.start_value.setText(str(sample.start_position))
            self.end_value.setText(str(sample.end_position))
