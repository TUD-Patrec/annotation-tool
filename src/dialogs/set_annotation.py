import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

import sys, logging
import numpy as np

class QAnnotationDialog(qtw.QDialog):
    new_annotation = qtc.pyqtSignal(dict)
    
    def __init__(self, groups, dependencies):
        super(qtw.QWidget, self).__init__()
        self.groups = groups
        self.dependencies = dependencies
        self.buttons, self.button_to_idx_map = self.__init_buttons__()
        self.elements_per_row = None
        
        
        self.accept_button = qtw.QPushButton()
        self.cancel_button = qtw.QPushButton()
        
        self.resize(930, 800)
        
        self.N = len(self.buttons)
        self.current_selection = np.zeros(self.N, dtype=np.uint8)
        self.idx_scrollWidget_map = dict()
        
        self.setLayout(qtw.QVBoxLayout())
        
        self.bottom_widget = self.__init_navigation_buttons__()
        
        self.__init_layout__()
        self.layout().addWidget(self.top_widget, stretch=1)
        self.layout().addWidget(self.bottom_widget)
        qtc.QTimer.singleShot(0, self.__resize__)
        
  
    def set_annotation(self, annotation):
        if type(annotation) not in [dict, np.ndarray]:
            raise RuntimeError('Unknown type: {}'.format(type(annotation)))
        if type(annotation) == dict:
            self.current_selection = self.__dict_to_vector__(annotation)
        if type(annotation) == np.ndarray:
            assert annotation.shape == self.current_selection.shape
            self.current_selection = annotation
        for idx, x in enumerate(self.current_selection):
            btn : QPushButtonAdapted = self.buttons[idx]
            btn.setChecked(False)
            if x == 1:
                btn.click()
     
    def __vector_to_dict__(self, vec):
        annotation_dict = dict()
        
        offset = 0
        for group_name, group_elements in self.groups:
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
        for group_name, group_elements in self.groups:
            for elem in group_elements:
                vec.append(dictionary[group_name][elem])
                idx += 1
        return np.array(vec, dtype=np.uint8) 
        
    def __init_buttons__(self):
        idx = 0
        buttons = []
        button_to_idx_map = dict()
        for group_name, group_elements in self.groups:
            for elem in group_elements:
                button = QPushButtonAdapted(group_name, elem)
                button.setText(elem)
                button.button_clicked.connect(lambda x,y,z: self.__update_current_selection__(x,y,z))
                
                buttons.append(button)
                button_to_idx_map[(group_name, elem)] = idx
                
                idx += 1
        return buttons, button_to_idx_map
    
    def __init_layout__(self):
        self.top_widget = qtw.QWidget(self)
        self.top_widget.setLayout(qtw.QGridLayout())
        self.top_widget.layout().setColumnStretch(0, 0)
        self.top_widget.layout().setColumnStretch(1, 1)
        
        for idx, (name, _) in enumerate(self.groups):
            group_label = qtw.QLabel(name)
            
            scroll_area = qtw.QScrollArea(self)
            scroll_area.setAlignment(qtc.Qt.AlignLeft)
            
            scroll_widget = qtw.QWidget(self)
            scroll_widget.setLayout(qtw.QGridLayout())
            
            self.idx_scrollWidget_map[idx] = scroll_widget            # keeping a list of scroll_widgets for later update
            scroll_area.setWidget(scroll_widget)
            
            self.top_widget.layout().addWidget(group_label, idx, 0)
            self.top_widget.layout().addWidget(scroll_area, idx, 1)
            
    def __resize__(self):
        # check that at least one element group is existing
        if bool(self.idx_scrollWidget_map):
            scroll_aras = [self.idx_scrollWidget_map[idx].parent().parent() for idx in range(len(self.groups))]
            widths = [s.width() for s in scroll_aras]
            width = min(widths)
            
            scroll_widget= self.idx_scrollWidget_map[0]
            margin_l, margin_t, margin_r, margin_b = scroll_widget.layout().getContentsMargins()
            spacing = scroll_widget.layout().spacing()

            button_width = self.buttons[0].width()
            useable_width = width - margin_l - margin_r - 20        
            elements_per_row = (useable_width + spacing) // (button_width + spacing)
            elements_per_row = max(1, elements_per_row)
            
            
            if self.elements_per_row == elements_per_row:
                for idx in range(len(self.groups)):
                    scroll_widget = self.idx_scrollWidget_map[idx]
                    scroll_widget.adjustSize()
                return
            
            self.elements_per_row = elements_per_row
            offset = 0
            for group_idx, (group_name, group_elements) in enumerate(self.groups):
                scroll_widget = self.idx_scrollWidget_map[group_idx]
                                
                for i in reversed(range(scroll_widget.layout().count())):
                    scroll_widget.layout().itemAt(i).widget().setParent(None)
                    
                pos = 0
                for idx, elem in enumerate(group_elements):
                    row, col = pos // elements_per_row + 1, pos % elements_per_row
                    btn = self.buttons[offset + idx]
                    if btn.isCheckable():
                        scroll_widget.layout().addWidget(btn, row, col, alignment=qtc.Qt.AlignCenter)
                        pos += 1
                
                qtc.QTimer.singleShot(0, scroll_widget.adjustSize)
                offset += len(group_elements)
        else:
            logging.warning('Should not happen')
    
    def __update__(self):
        if self.elements_per_row is None:
            self.__resize__()
        
        offset = 0
        vec = self.__get_determined_attributes__()
        
        for group_idx, (group_name, group_elements) in enumerate(self.groups):
            scroll_widget= self.idx_scrollWidget_map[group_idx]
            
            for i in reversed(range(scroll_widget.layout().count())): 
                scroll_widget.layout().itemAt(i).widget().setParent(None)
                        
            elements_per_row = self.elements_per_row 
            
            pos = 0
            for idx, elem in enumerate(group_elements):
                btn = self.buttons[offset + idx]
                
                if vec[offset + idx] == -1 or self.current_selection[offset + idx] == 1:
                # the value of the attribute at that position is not yet determined
                    row, col = pos // elements_per_row + 1, pos % elements_per_row
                    btn.setParent(scroll_widget)
                    btn.setCheckable(True)
                    if self.current_selection[offset + idx] != 1:
                        btn.unhighlight()
                    scroll_widget.layout().addWidget(btn, row, col, alignment=qtc.Qt.AlignCenter)
                    pos += 1
                
                else:
                    if vec[offset + idx] == 1:
                        row, col = pos // elements_per_row + 1, pos % elements_per_row
                        btn.setParent(scroll_widget)
                        btn.setCheckable(False)
                        btn.highlight()
                        scroll_widget.layout().addWidget(btn, row, col, alignment=qtc.Qt.AlignCenter)
                        pos += 1
                    else:
                        btn.setParent(None)
                        btn.setCheckable(False)
                        btn.unhighlight()
            qtc.QTimer.singleShot(0, scroll_widget.adjustSize)
            offset += len(group_elements)
        self.check_selection_valid()
                 
    def resizeEvent(self, event):
        qtw.QWidget.resizeEvent(self, event)
        self.__resize__()
        
    def __init_navigation_buttons__(self):
        widget = qtw.QWidget()
        hbox = qtw.QHBoxLayout()
        widget.setLayout(hbox)
               
        btn_hight = 50
        
        self.accept_button.clicked.connect(lambda _: self.__save_annotation__())
        self.accept_button.setFixedHeight(btn_hight)
        self.accept_button.setText('Save Annotation')
        hbox.addWidget(self.accept_button)
        
        self.cancel_button.clicked.connect(lambda _: self.__cancel_annotation__())
        self.cancel_button.setText('Cancel')
        self.cancel_button.setFixedHeight(btn_hight)
        hbox.addWidget(self.cancel_button)
        
        return widget
        
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
            raise RuntimeError('there must always be at least 1 possible combination left over!')
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
        if self.dependencies is None:
            attr_vec = self.current_selection
        else:
            attr_vec = self.get_current_vector()
        
        annotation_dict = self.__vector_to_dict__(attr_vec)
        
        #print(annotation_dict)
        #print(self.__print_combination__(attr_vec))
            
        self.new_annotation.emit(annotation_dict)
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
        
        self.checked_style = "border-color: green"
        self.highlight_style = "border-color: gold"
        self.unchecked_style = "width: 250"
        self.setStyleSheet(self.unchecked_style)
        self.setFixedWidth(250)
        
        self.clicked.connect(lambda _: self.btn_clicked())
        
    def btn_clicked(self):
        is_checked = self.isChecked()
        if is_checked:
            self.setStyleSheet(self.checked_style)
        else:
            self.setStyleSheet(self.unchecked_style)
        self.button_clicked.emit(self.group_name, self.element_name, is_checked)
        
    def highlight(self):
        self.setStyleSheet(self.highlight_style)
     
    def unhighlight(self):
        self.setStyleSheet(self.unchecked_style)
    
    
if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)

    
    groups = []
    
    #dependencies = np.random.randint(0,2, (5000, 200))
    
    dependencies = np.loadtxt('C:\\Users\\Raphael\\Desktop\\Dev\\annotation_tool\\datasets\\Kitchen_Dataset\\dependencies.csv', delimiter=',', dtype=np.uint8)
    import json
    with open('C:\\Users\\Raphael\\Desktop\\Dev\\annotation_tool\\datasets\\Kitchen_Dataset\\scheme.json') as f:
        scheme = json.load(f)
        
    for g, g_elems in scheme:
        for idx, v in enumerate(g_elems):
            v : str = v
            if v.find('&') != -1:
                g_elems[idx] = v.replace('&', ' AND ')
    
    
    widget = QAnnotationDialog(scheme, None)
    
    test_vec = np.zeros(dependencies.shape[1])
    test_vec[-1] = 1
    # widget.set_annotation(test_vec)
    
    #widget.resize(400,300)
    widget.show()
    #widget.__update__()

    sys.exit(app.exec_())
