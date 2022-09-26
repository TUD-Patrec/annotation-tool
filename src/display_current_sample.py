import logging

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from .qt_helper_widgets.adaptive_scroll_area import QAdaptiveScrollArea
from .qt_helper_widgets.lines import QHLine


class QDisplaySample(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(QDisplaySample, self).__init__(*args, **kwargs)
        self.scheme = None
        self.sample = None
        self.scroll_widgets = []

        self.top_widget = qtw.QLabel("CURRENT SAMPLE", alignment=qtc.Qt.AlignCenter)

        self.start_label = qtw.QLabel("Start Frame:", alignment=qtc.Qt.AlignCenter)
        self.start_value = qtw.QLabel("A", alignment=qtc.Qt.AlignCenter)
        self.end_label = qtw.QLabel("End Frame:", alignment=qtc.Qt.AlignCenter)
        self.end_value = qtw.QLabel("B", alignment=qtc.Qt.AlignCenter)

        self.middle_widget = qtw.QWidget()
        self.middle_widget.setLayout(qtw.QHBoxLayout())

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
        self.__update__()

    def set_annotation(self, annotation):
        self.scheme = annotation.dataset.scheme
        self.sample = None
        self.__update__()

    def set_selected(self, sample):
        self.sample = sample
        self.__update__()

    def __update__(self):
        if self.sample is None:
            widget = qtw.QLabel(
                "There is no sample to show yet.", alignment=qtc.Qt.AlignCenter
            )
            self.layout().replaceWidget(self.middle_widget, widget)
            self.middle_widget.setParent(None)
            self.middle_widget = widget
            self.start_value.setText(str(0))
            self.end_value.setText(str(0))

        # Case 2: Sample is not annotated yet
        elif not self.sample.annotation_exists:
            widget = qtw.QLabel(
                "The sample is not annotated yet.", alignment=qtc.Qt.AlignCenter
            )
            self.layout().replaceWidget(self.middle_widget, widget)
            self.middle_widget.setParent(None)
            self.middle_widget = widget
            self.start_value.setText(str(self.sample.start_position))
            self.end_value.setText(str(self.sample.end_position))

        # Case 3: Sample and scheme loaded
        else:
            widget = qtw.QWidget(self)
            grid = qtw.QGridLayout()
            grid.setColumnStretch(1, 1)

            for idx, (group_name, group_elements) in enumerate(self.scheme):
                scroll_wid = QAdaptiveScrollArea(self)

                for elem in group_elements:
                    if self.sample.annotation[group_name][elem] == 1:
                        lbl = qtw.QLabel(elem, alignment=qtc.Qt.AlignCenter)
                        lbl.setAlignment(qtc.Qt.AlignCenter)
                        scroll_wid.addItem(lbl)

                txt = group_name.upper() + ":"
                name_label = qtw.QLabel(txt)

                grid.addWidget(name_label, idx, 0)
                grid.addWidget(scroll_wid, idx, 1)

            widget.setLayout(grid)

            self.layout().replaceWidget(self.middle_widget, widget)
            self.middle_widget.setParent(None)
            self.middle_widget = widget
            self.start_value.setText(str(self.sample.start_position))
            self.end_value.setText(str(self.sample.end_position))


if __name__ == "__main__":
    import sys

    app = qtw.QApplication(sys.argv)

    widget = QDisplaySample()

    import data_classes.sample as sample

    widget.set_sample(sample.Sample(0, 100, None))
    widget.set_sample(sample.Sample(50, 250, None))

    # widget.resize(400,300)
    widget.show()

    sys.exit(app.exec_())
