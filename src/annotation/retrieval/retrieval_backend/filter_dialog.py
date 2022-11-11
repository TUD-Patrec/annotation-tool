import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import numpy as np

from src.annotation.retrieval.retrieval_backend.filter import FilterCriterion
from src.qt_helper_widgets.checkable_combobox import CheckableComboBox


class QRetrievalFilter(qtw.QDialog):
    filter_changed = qtc.pyqtSignal(FilterCriterion)

    def __init__(self, old_filter, scheme, *args, **kwargs):
        super(QRetrievalFilter, self).__init__(*args, **kwargs)
        self.old_filter = old_filter
        self.scheme = scheme
        self.init_UI()

    def init_UI(self):
        self.form = qtw.QFormLayout(self)
        self.combo_boxes = []

        last_element = None
        for idx, scheme_element in enumerate(self.scheme):
            if last_element is None or last_element.row != scheme_element.row:
                combo_box = CheckableComboBox()
                self.combo_boxes.append(combo_box)
                self.form.addRow(scheme_element.group_name.upper() + ":", combo_box)

            combo_box.addItem(scheme_element.element_name)

            if not self.old_filter.is_empty():
                is_checked = self.old_filter.filter_array[idx] == 1
                if is_checked:
                    combo_box.model().item(scheme_element.column).setCheckState(
                        qtc.Qt.Checked
                    )

            last_element = scheme_element

        self.accept_button = qtw.QPushButton("Save")
        self.accept_button.clicked.connect(self.accept_clicked)
        self.form.addRow(self.accept_button)

        self.setMinimumWidth(500)

    def accept_clicked(self):
        filter_array = np.zeros(len(self.scheme))

        for idx, scheme_element in enumerate(self.scheme):
            combo_box = self.combo_boxes[scheme_element.row]
            current_data = combo_box.currentData()
            if scheme_element.element_name in current_data:
                filter_array[idx] = 1

        new_filter = FilterCriterion(filter_array)

        if new_filter != self.old_filter:
            self.filter_changed.emit(new_filter)

        self.close()
