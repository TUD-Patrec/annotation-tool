import logging
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import numpy as np

from .adaptive_scroll_area import QAdaptiveScrollArea
from textwrap import wrap


class QShowAnnotation(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(QShowAnnotation, self).__init__(*args, **kwargs)
        self.grid = qtw.QGridLayout(self)

    def show_annotation(self, scheme, annotation):
        if type(annotation) is dict:
            annotation = self.dict_to_array(scheme, annotation)

        assert type(annotation) is np.ndarray

        for i in reversed(range(self.grid.count())):
            widgetToRemove = self.grid.itemAt(i).widget()
            # remove it from the layout list
            self.grid.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        assert self.grid.count() == 0

        offset = 0
        for idx, (group_name, group_elements) in enumerate(scheme):
            scroll_wid = QAdaptiveScrollArea(self)

            c = 0
            for elem_idx, elem in enumerate(group_elements):
                adjusted_idx = offset + elem_idx
                if annotation[adjusted_idx] == 1:

                    attr_name = self.format_str(elem, 25, line_start=f"- ")

                    lbl = qtw.QLabel(attr_name, alignment=qtc.Qt.AlignCenter)
                    lbl.setFixedWidth(200)
                    lbl.setAlignment(qtc.Qt.AlignLeft)
                    scroll_wid.addItem(lbl)

                    c += 1

            group_name = self.format_str("".join([group_name.upper(), ":"]), 25)
            name_label = qtw.QLabel(group_name)
            name_label.setFixedWidth(200)

            self.grid.addWidget(name_label, idx, 0)
            self.grid.addWidget(scroll_wid, idx, 1)

            offset += len(group_elements)

    def format_str(self, s, characters_per_line, line_start=""):
        ls = wrap(s, characters_per_line)
        for idx, line in enumerate(ls):
            if idx == 0:
                ls[idx] = "".join([line_start, line])
            else:
                ls[idx] = "".join([" " * len(line_start), line])
        return "\n".join(ls)

    def dict_to_array(self, scheme, d):
        ls = []
        for name, elements in scheme:
            for e in elements:
                ls.append(d[name][e])
        return np.array(ls, dtype=np.int8)
