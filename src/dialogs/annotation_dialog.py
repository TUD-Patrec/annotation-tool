import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import sys
import logging
import numpy as np


class QAnnotationDialog(qtw.QDialog):
    new_annotation = qtc.pyqtSignal(dict)

    def __init__(self, scheme, dependencies, annotation=None, *args, **kwargs):
        super(QAnnotationDialog, self).__init__(*args, **kwargs)
        self.scheme = scheme
        self.dependencies = dependencies

        self.init_top_widget()
        self.init_bottom_widget()

        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.top_widget, stretch=1)
        self.layout.addWidget(self.bottom_widget)

        self.N = len(self.buttons)
        self.current_selection = np.zeros(self.N, dtype=np.uint8)

        if annotation:
            self._set_annotation(annotation)

    def _set_annotation(self, annotation):
        if type(annotation) not in [dict, np.ndarray]:
            raise RuntimeError("Unknown type: {}".format(type(annotation)))
        if type(annotation) == dict:
            self.current_selection = self.__dict_to_vector__(annotation)
        if type(annotation) == np.ndarray:
            assert annotation.shape == self.current_selection.shape
            self.current_selection = annotation
        for idx in np.nonzero(self.current_selection)[0]:
            btn: QPushButtonAdapted = self.buttons[idx]
            btn.setChecked(False)
            btn.click()

    def __vector_to_dict__(self, vec):
        annotation_dict = dict()

        offset = 0
        for group_name, group_elements in self.scheme:
            group_dict = dict()
            annotation_dict[group_name] = group_dict
            for idx, group_elem in enumerate(group_elements):
                vec_pos = offset + idx
                value = vec[vec_pos]
                group_dict[group_elem] = value
            offset += len(group_elements)

        return annotation_dict

    def __dict_to_vector__(self, dictionary):
        vec = []
        idx = 0
        for group_name, group_elements in self.scheme:
            for elem in group_elements:
                vec.append(dictionary[group_name][elem])
                idx += 1
        return np.array(vec, dtype=np.uint8)

    def init_top_widget(self):
        self.scroll_widgets = []

        self.top_widget = qtw.QWidget(self)
        self.top_widget.layout = qtw.QGridLayout(self.top_widget)
        self.top_widget.layout.setColumnStretch(1, 1)
        self.top_widget.layout.setRowStretch(0, 1)

        idx = 0
        self.buttons = []
        self.button_to_idx_map = dict()
        for group_idx, (group_name, group_elements) in enumerate(self.scheme):
            group_buttons = []
            for elem in group_elements:
                button = QPushButtonAdapted(group_name, elem)
                elem_txt = elem.replace("&", " && ")
                button.setText(elem_txt)

                button.button_clicked.connect(
                    lambda x, y, z: self.__update_current_selection__(x, y, z)
                )

                self.buttons.append(button)
                self.button_to_idx_map[(group_name, elem)] = idx

                group_buttons.append(button)
                idx += 1
            new_scroll_widget = QAdaptiveScrollArea(
                group_buttons, no_scroll=group_idx == 0 or len(group_buttons) < 10
            )
            self.scroll_widgets.append(new_scroll_widget)

            lbl = qtw.QLabel()
            lbl.setAlignment(qtc.Qt.AlignCenter)
            lbl.setText(group_name.upper() + ":")

            self.top_widget.layout.addWidget(lbl, group_idx, 0)
            self.top_widget.layout.addWidget(new_scroll_widget, group_idx, 1)

    def init_bottom_widget(self):
        self.bottom_widget = qtw.QWidget(self)
        hbox = qtw.QHBoxLayout(self.bottom_widget)
        self.bottom_widget.setLayout(hbox)

        self.accept_button = qtw.QPushButton(self)
        self.accept_button.clicked.connect(lambda _: self.__save_annotation__())
        self.accept_button.setText("Save")
        hbox.addWidget(self.accept_button)

        self.reset_button = qtw.QPushButton(self)
        self.reset_button.clicked.connect(lambda _: self.__reset_annotation__())
        self.reset_button.setText("Reset")
        hbox.addWidget(self.reset_button)

        self.cancel_button = qtw.QPushButton(self)
        self.cancel_button.clicked.connect(lambda _: self.__cancel_annotation__())
        self.cancel_button.setText("Cancel")
        hbox.addWidget(self.cancel_button)

    def __update__(self):
        if self.dependencies is None or len(self.dependencies) == 0:
            # Nothing to update here
            return

        offset = 0
        vec = self.__get_determined_attributes__()

        for _, group_elements in self.scheme:
            for idx, _ in enumerate(group_elements):
                effective_idx = offset + idx
                btn = self.buttons[effective_idx]

                if (
                    vec[effective_idx] == -1
                    or self.current_selection[effective_idx] == 1
                ):
                    # the value of the attribute at that position is not yet determined
                    btn.setCheckable(True)
                    if self.current_selection[effective_idx] != 1:
                        btn.unhighlight()
                else:
                    if vec[effective_idx] == 1:
                        btn.setCheckable(False)
                        btn.highlight()
                    else:
                        btn.setCheckable(False)
                        btn.unhighlight()
            offset += len(group_elements)
        for wid in self.scroll_widgets:
            wid.updateUI()

        self.check_selection_valid()

    def __init_current_selection__(self):
        N = len(self.buttons)
        self.current_selection = np.zeros(N, dtype=np.uint8)

    def __update_current_selection__(self, row, col, is_checked):
        idx = self.button_to_idx_map[(row, col)]
        self.current_selection[idx] = int(is_checked)
        self.__update__()

    def __get_determined_attributes__(self):
        if self.dependencies is None:
            return np.zeros(self.N, dtype=np.int8) - 1
        else:
            arr = []

            columns = self.__get_possible_combinations__().transpose()
            for col in columns:
                unique_values = np.unique(col)
                n_different_values_occured = unique_values.shape[0]
                assert 1 <= n_different_values_occured <= 2
                is_determined = n_different_values_occured == 1
                if is_determined:
                    arr.append(unique_values[0])
                else:
                    arr.append(-1)
            return np.array(arr, dtype=np.int8)

    def __get_possible_combinations__(self):
        dependencies = self.dependencies
        vec2 = self.current_selection

        comb = []

        for vec1 in dependencies:
            res = np.logical_and(vec1, vec2)
            if np.array_equal(res, vec2):
                comb.append(vec1)

        if len(comb) == 0:
            raise RuntimeError(
                "there must always be at least 1 possible combination left over!"
            )
        if len(comb) == 1:
            self.accept_button.setEnabled(True)
        if len(comb) > 1:
            self.accept_button.setEnabled(False)

        return np.array(comb)

    def get_current_vector(self):
        comb_vec = self.__get_determined_attributes__()
        attr_vec = np.copy(self.current_selection)
        for idx in range(attr_vec.shape[0]):
            attr_vec[idx] = attr_vec[idx] if comb_vec[idx] == -1 else comb_vec[idx]
        return attr_vec

    def check_selection_valid(self):
        arr = self.dependencies
        if arr is None:
            self.accept_button.setEnabled(True)
        else:
            attr_vec = self.get_current_vector()
            x = np.equal(attr_vec, arr).all(axis=1).any()
            # print('VALID = ', x)
            self.accept_button.setEnabled(x)

    def __save_annotation__(self):
        # Empty Annotation -> Reset Sample
        if not np.any(self.current_selection):
            self.new_annotation.emit({})
            self.close()

        # Default Case
        else:
            if self.dependencies is None:
                attr_vec = self.current_selection
            else:
                attr_vec = self.get_current_vector()

            annotation_dict = self.__vector_to_dict__(attr_vec)
            self.new_annotation.emit(annotation_dict)
            self.close()

    def __reset_annotation__(self):
        # for idx in np.nonzero(self.current_selection)[0]:
        #    btn : QPushButtonAdapted = self.buttons[idx]
        #    if btn.isChecked():
        #        btn.click()
        # self.__update__()
        self.new_annotation.emit({})
        self.close()

    def __cancel_annotation__(self):
        self.close()


class QPushButtonAdapted(qtw.QPushButton):
    button_clicked = qtc.pyqtSignal(str, str, bool)

    def __init__(self, group_name, element_name):
        super(qtw.QWidget, self).__init__()
        self.setCheckable(True)
        self.group_name = group_name
        self.element_name = element_name
        self.is_highlighted = False

        self.checked_style = "border-color: green"
        self.highlight_style = "border-color: gold"
        self.unchecked_style = ""
        self.setStyleSheet(self.unchecked_style)

        self.clicked.connect(lambda _: self.btn_clicked())

    def btn_clicked(self):
        is_checked = self.isChecked()
        if is_checked:
            self.setStyleSheet(self.checked_style)
        else:
            self.setStyleSheet(self.unchecked_style)
        self.button_clicked.emit(self.group_name, self.element_name, is_checked)

    def highlight(self):
        self.is_highlighted = True
        self.setStyleSheet(self.highlight_style)

    def unhighlight(self):
        self.is_highlighted = False
        self.setStyleSheet(self.unchecked_style)


class QAdaptiveScrollArea(qtw.QWidget):
    def __init__(self, buttons, no_scroll=False, parent=None):
        super(QAdaptiveScrollArea, self).__init__(parent=parent)
        self.buttons = buttons
        self.elements_per_row = 3
        self.no_scroll = no_scroll
        self.initUI()

    def initUI(self):
        for btn in self.buttons:
            btn.setParent(None)

        if self.no_scroll:
            self.layout = qtw.QHBoxLayout(self)
            self.scrollAreaWidgetContents = qtw.QWidget()
            self.gridLayout = qtw.QGridLayout(self.scrollAreaWidgetContents)
            self.layout.addWidget(self.scrollAreaWidgetContents)

            for idx, btn in enumerate(
                filter(lambda x: x.isCheckable() or x.is_highlighted, self.buttons)
            ):
                row, col = idx // self.elements_per_row + 1, idx % self.elements_per_row
                self.gridLayout.addWidget(btn, row, col)

        else:
            self.layout = qtw.QHBoxLayout(self)
            self.scrollArea = qtw.QScrollArea(self)
            self.scrollArea.setWidgetResizable(True)
            self.scrollAreaWidgetContents = qtw.QWidget()
            self.gridLayout = qtw.QGridLayout(self.scrollAreaWidgetContents)
            self.scrollArea.setWidget(self.scrollAreaWidgetContents)
            self.layout.addWidget(self.scrollArea)

            # self.scrollArea.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOn)

            for idx, btn in enumerate(
                filter(lambda x: x.isCheckable() or x.is_highlighted, self.buttons)
            ):
                row, col = idx // self.elements_per_row + 1, idx % self.elements_per_row
                self.gridLayout.addWidget(btn, row, col)

    def updateUI(self):
        for btn in self.buttons:
            btn.setParent(None)

        if self.no_scroll:
            old_w = self.scrollAreaWidgetContents
            self.scrollAreaWidgetContents = qtw.QWidget()
            self.gridLayout = qtw.QGridLayout(self.scrollAreaWidgetContents)

            self.layout.replaceWidget(old_w, self.scrollAreaWidgetContents)

            for idx, btn in enumerate(
                filter(lambda x: x.isCheckable() or x.is_highlighted, self.buttons)
            ):
                row, col = idx // self.elements_per_row + 1, idx % self.elements_per_row
                self.gridLayout.addWidget(btn, row, col)

        else:
            self.scrollAreaWidgetContents = qtw.QWidget()
            self.gridLayout = qtw.QGridLayout(self.scrollAreaWidgetContents)

            self.scrollArea.setWidget(self.scrollAreaWidgetContents)

            for idx, btn in enumerate(
                filter(lambda x: x.isCheckable() or x.is_highlighted, self.buttons)
            ):
                row, col = idx // self.elements_per_row + 1, idx % self.elements_per_row
                self.gridLayout.addWidget(btn, row, col)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)

    groups = []

    # dependencies = np.random.randint(0,2, (5000, 200))

    dependencies = np.loadtxt(
        "C:\\Users\\Raphael\\Desktop\\Dev\\__annotation_tool\\datasets\\Kitchen_Dataset\\dependencies.csv",
        delimiter=",",
        dtype=np.uint8,
    )
    import json

    with open(
        "C:\\Users\\Raphael\\Desktop\\Dev\\__annotation_tool\\datasets\\Kitchen_Dataset\\scheme.json"
    ) as f:
        scheme = json.load(f)

    widget = QAnnotationDialog(scheme, dependencies)

    test_vec = np.zeros(dependencies.shape[1])
    test_vec[-1] = 1
    # widget.set_annotation(test_vec)

    # widget.resize(400,300)
    widget.show()
    # widget.__update__()

    sys.exit(app.exec_())
