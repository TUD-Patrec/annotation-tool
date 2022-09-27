import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import numpy as np

from src.qt_helper_widgets.checkable_combobox import CheckableComboBox


class QRetrievalFilter(qtw.QDialog):
    filter_changed = qtc.pyqtSignal(np.ndarray)

    def __init__(self, filter_vector, scheme, *args, **kwargs):
        super(QRetrievalFilter, self).__init__(*args, **kwargs)
        self.filter_vector = filter_vector
        self.scheme = scheme

        self.init_UI()

    def init_UI(self):
        self.form = qtw.QFormLayout(self)

        self.combo_boxes = []

        idx = 0
        for gr_name, gr_elems in self.scheme:
            combo_box = CheckableComboBox()

            for elem in gr_elems:
                combo_box.addItem(elem)
                if self.filter_vector:
                    if self.filter_vector[idx] == 1:
                        pass
                idx += 1

            self.combo_boxes.append(combo_box)

            self.form.addRow(gr_name.upper() + ":", combo_box)

        self.accept_button = qtw.QPushButton("Save")
        self.accept_button.clicked.connect(self.accept_clicked)
        self.form.addRow(self.accept_button)

        self.setMinimumWidth(500)

    def accept_clicked(self):
        new_filter = self.empty_vec_for_scheme()
        offset = 0
        for idx, combo_box in enumerate(self.combo_boxes):
            current_data = combo_box.currentData()
            for inner_idx, elem in enumerate(self.scheme[idx][1]):
                if elem in current_data:
                    adjusted_index = offset + inner_idx
                    new_filter[adjusted_index] = 1
            offset += len(self.scheme[idx][1])
        if self.filter_vector is None or np.array_equal(new_filter, self.filter_vector):
            self.filter_changed.emit(new_filter)
        self.close()

    def empty_vec_for_scheme(self):
        if self.filter_vector:
            return np.zeros_like(self.filter_vector)
        length = 0
        for _, elems in self.scheme:
            length += len(elems)
        return np.zeros(length)
