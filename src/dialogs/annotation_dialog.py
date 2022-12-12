import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import numpy as np

from src.data_model import AnnotationScheme, Sample
from src.data_model.annotation import Annotation

preferred_size = None


class QAnnotationDialog(qtw.QDialog):
    def __init__(
        self,
        sample: Sample,
        scheme: AnnotationScheme,
        dependencies: np.ndarray = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.sample = sample
        self.scheme = scheme
        self.dependencies = dependencies

        self.init_top_widget()
        self.init_bottom_widget()

        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.top_widget, stretch=1)
        self.layout.addWidget(self.bottom_widget)

        self.N = len(self.buttons)
        self.current_selection = np.zeros(self.N, dtype=np.uint8)

        self._set_annotation(sample.annotation)

        if preferred_size is not None:
            print("Setting preferred size")
            self.resize(preferred_size)

    def _set_annotation(self, a):
        self.current_selection = np.copy(a.annotation_vector)
        for idx in np.nonzero(self.current_selection)[0]:
            btn: QPushButtonAdapted = self.buttons[idx]
            btn.setChecked(False)
            btn.click()

    def tmp(self, last_elem, group_buttons):
        no_scroll = last_elem.row == 0 or len(group_buttons) < 10
        new_scroll_widget = QAdaptiveScrollArea(group_buttons, no_scroll=no_scroll)
        self.scroll_widgets.append(new_scroll_widget)

        lbl = qtw.QLabel()
        lbl.setAlignment(qtc.Qt.AlignCenter)
        lbl.setText(last_elem.group_name.upper() + ":")

        self.top_widget.layout.addWidget(lbl, last_elem.row, 0)
        self.top_widget.layout.addWidget(new_scroll_widget, last_elem.row, 1)

    def init_top_widget(self):
        self.scroll_widgets = []

        self.top_widget = qtw.QWidget(self)
        self.top_widget.layout = qtw.QGridLayout(self.top_widget)
        self.top_widget.layout.setColumnStretch(1, 1)
        self.top_widget.layout.setRowStretch(0, 1)

        idx = 0
        self.buttons = []
        self.button_to_idx_map = {}

        group_buttons = []
        last_elem = None
        for idx, scheme_element in enumerate(self.scheme):
            if last_elem is not None and scheme_element.row != last_elem.row:
                self.tmp(last_elem, group_buttons)
                group_buttons = []

            button = QPushButtonAdapted(
                scheme_element.group_name, scheme_element.element_name
            )
            elem_txt = scheme_element.element_name.replace("&", " && ")
            button.setText(elem_txt)

            button.button_clicked.connect(
                lambda x, y, z: self.__update_current_selection__(x, y, z)
            )

            self.buttons.append(button)
            self.button_to_idx_map[
                (scheme_element.group_name, scheme_element.element_name)
            ] = idx

            group_buttons.append(button)

            last_elem = scheme_element
        if idx > 0:
            self.tmp(last_elem, group_buttons)

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

        vec = self.__get_determined_attributes__()

        for idx, scheme_element in enumerate(self.scheme):
            btn = self.buttons[idx]

            if vec[idx] == -1 or self.current_selection[idx] == 1:
                # the value of the attribute at that position is not yet determined
                btn.setCheckable(True)
                if self.current_selection[idx] != 1:
                    btn.unhighlight()
            else:
                if vec[idx] == 1:
                    btn.setCheckable(False)
                    btn.highlight()
                else:
                    btn.setCheckable(False)
                    btn.unhighlight()
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

    def __reset_annotation__(self):
        self.sample.annotation = Annotation(self.scheme)
        self.close()

    def __save_annotation__(self):
        # Empty Annotation -> Reset Sample
        if not np.any(self.current_selection):
            self.__reset_annotation__()
            return
        # Default Case
        else:
            if self.dependencies is None:
                attr_vec = self.current_selection
            else:
                attr_vec = self.get_current_vector()

        anno = self.sample.annotation
        anno.annotation = attr_vec

        self.sample.annotation = anno
        self.close()

    def __cancel_annotation__(self):
        self.close()

    def resizeEvent(self, a0) -> None:
        global preferred_size
        preferred_size = self.size()
        return super().resizeEvent(a0)


class QPushButtonAdapted(qtw.QPushButton):
    button_clicked = qtc.pyqtSignal(str, str, bool)

    def __init__(self, group_name, element_name):
        super(qtw.QWidget, self).__init__()
        self.setCheckable(True)
        self.group_name = group_name
        self.element_name = element_name
        self.is_highlighted = False

        # self.checked_style = "border-color: green"
        # self.highlight_style = "border-color: gold"

        self.checked_style = (
            "border-color: green; border-width: 2px; border-style: solid;"
        )
        self.highlight_style = (
            "border-color: gold; border-width: 2px; border-style: solid;"
        )
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
        super().__init__(parent=parent)
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
