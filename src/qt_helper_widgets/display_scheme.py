import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from .adaptive_scroll_area import QAdaptiveScrollArea
from textwrap import wrap


def format_str(s, characters_per_line, line_start=""):
    ls = wrap(s, characters_per_line)
    for idx, line in enumerate(ls):
        if idx == 0:
            ls[idx] = "".join([line_start, line])
        else:
            ls[idx] = "".join([" " * len(line_start), line])
    return "\n".join(ls)


class QShowAnnotation(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(QShowAnnotation, self).__init__(*args, **kwargs)
        # self.grid = qtw.QGridLayout(self)
        self.form = qtw.QFormLayout(self)

    def show_annotation(self, annotation):
        self.reset_layout()

        current_row = -1

        for attribute in annotation:
            if attribute.row != current_row:
                current_row = attribute.row
                list_widget = qtw.QListWidget()
                list_widget.setDisabled(True)
                list_widget.setItemAlignment(qtc.Qt.AlignCenter)

                group_name = attribute.group_name.capitalize() + ":"
                name_label = qtw.QLabel(group_name)

                self.form.addRow(group_name, list_widget)

            if attribute.value == 1:
                list_item = qtw.QListWidgetItem(attribute.element_name)
                list_item.setTextAlignment(qtc.Qt.AlignCenter)
                list_widget.addItem(list_item)

    def show_annotation2(self, annotation):
        self.reset_layout()

        current_row = -1

        for attribute in annotation:
            if attribute.row != current_row:
                scroll_wid = QAdaptiveScrollArea(self)
                current_row = attribute.row

                group_name = format_str(
                    "".join([attribute.group_name.upper(), ":"]), 25
                )
                name_label = qtw.QLabel(group_name)
                name_label.setFixedWidth(100)

                self.grid.addWidget(name_label, attribute.row, 0)
                self.grid.addWidget(scroll_wid, attribute.row, 1)

            if attribute.value == 1:
                attr_name = format_str(attribute.element_name, 25, line_start=f"")
                lbl = qtw.QLabel(attr_name, alignment=qtc.Qt.AlignCenter)
                lbl.setFixedWidth(100)
                lbl.setAlignment(qtc.Qt.AlignLeft)
                scroll_wid.addItem(lbl)

    def reset_layout(self):
        for i in reversed(range(self.form.count())):
            widgetToRemove = self.form.itemAt(i).widget()
            # remove it from the layout list
            self.form.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        assert self.form.count() == 0

    def reset_layout2(self):
        for i in reversed(range(self.grid.count())):
            widgetToRemove = self.grid.itemAt(i).widget()
            # remove it from the layout list
            self.grid.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        assert self.grid.count() == 0
