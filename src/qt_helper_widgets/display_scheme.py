from textwrap import wrap

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


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
        super().__init__(*args, **kwargs)
        self.form = qtw.QFormLayout(self)

    def show_annotation(self, annotation):
        self.reset_layout()

        if annotation is None or annotation.is_empty():
            label = qtw.QLabel("No annotation to show.", alignment=qtc.Qt.AlignCenter)
            self.form.addWidget(label)
            return

        current_row = -1

        for attribute in annotation:
            if attribute.row != current_row:
                current_row = attribute.row
                list_widget = qtw.QListWidget()
                list_widget.setMaximumHeight(50)
                list_widget.setDisabled(False)
                list_widget.setSelectionMode(qtw.QAbstractItemView.NoSelection)
                list_widget.setItemAlignment(qtc.Qt.AlignCenter)

                group_name = attribute.group_name.capitalize() + ":"

                self.form.addRow(group_name, list_widget)

            if attribute.value == 1:
                list_item = qtw.QListWidgetItem(attribute.element_name)
                list_item.setTextAlignment(qtc.Qt.AlignCenter)
                list_widget.addItem(list_item)

            list_widget.sortItems()

    def reset_layout(self):
        for i in reversed(range(self.form.count())):
            widgetToRemove = self.form.itemAt(i).widget()
            # remove it from the layout list
            self.form.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        assert self.form.count() == 0
