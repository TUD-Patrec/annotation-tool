import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw

from annotation_tool.data_model import Sample
from annotation_tool.qt_helper_widgets.display_scheme import QShowAnnotation
from annotation_tool.qt_helper_widgets.lines import QHLine


class QDisplaySample(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(QDisplaySample, self).__init__(*args, **kwargs)
        self.init_UI()

    def init_UI(self):
        self.top_widget = qtw.QLabel(
            "CURRENT SAMPLE", alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )

        self.start_label = qtw.QLabel(
            "Start Frame:", alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )
        self.start_value = qtw.QLabel("", alignment=qtc.Qt.AlignmentFlag.AlignCenter)
        self.end_label = qtw.QLabel(
            "End Frame:", alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )
        self.end_value = qtw.QLabel("", alignment=qtc.Qt.AlignmentFlag.AlignCenter)

        self.delta_label = qtw.QLabel(
            "Total Frames:", alignment=qtc.Qt.AlignmentFlag.AlignCenter
        )

        self.delta_value = qtw.QLabel("", alignment=qtc.Qt.AlignmentFlag.AlignCenter)

        self.middle_widget = QShowAnnotation(self)

        self.bottom_left_widget = qtw.QWidget()
        self.bottom_left_widget.setLayout(qtw.QFormLayout())
        self.bottom_left_widget.layout().addRow(self.start_label, self.start_value)
        self.bottom_left_widget.layout().addRow(self.end_label, self.end_value)
        self.bottom_left_widget.layout().addRow(self.delta_label, self.delta_value)

        self.bottom_right_widget = qtw.QWidget()
        self.bottom_right_widget.setLayout(qtw.QVBoxLayout())

        self.bottom_widget = qtw.QWidget()
        self.bottom_widget.setLayout(qtw.QHBoxLayout())
        self.bottom_widget.layout().addWidget(self.bottom_left_widget)
        self.bottom_widget.layout().addWidget(self.bottom_right_widget)

        vbox = qtw.QVBoxLayout()
        vbox.addWidget(self.top_widget, alignment=qtc.Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(
            self.middle_widget, alignment=qtc.Qt.AlignmentFlag.AlignCenter, stretch=1
        )
        vbox.addWidget(QHLine())
        vbox.addWidget(self.bottom_widget, alignment=qtc.Qt.AlignmentFlag.AlignCenter)

        self.setLayout(vbox)
        self.setFixedWidth(400)

    @qtc.pyqtSlot(list, Sample)
    def setSelected(self, _, sample):
        if sample is None:
            self.middle_widget.show_annotation(None)
            self.start_value.setText(str(0))
            self.end_value.setText(str(0))
            self.delta_value.setText(str(0))
        else:
            self.middle_widget.show_annotation(sample.annotation)
            self.start_value.setText(str(sample.start_position))
            self.end_value.setText(str(sample.end_position))
            self.delta_value.setText(
                str(sample.end_position - sample.start_position + 1)
            )

    @qtc.pyqtSlot(bool)
    def setEnabled(self, a0: bool) -> None:
        pass
