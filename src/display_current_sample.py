import logging
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg


class QDisplaySample(qtw.QWidget):    
    def __init__(self, *args, **kwargs):
        super(QDisplaySample, self).__init__(*args, **kwargs)
        self.scheme = None
        self.sample = None
        
        self.top_widget = qtw.QLabel('CURRENT SAMPLE', alignment=qtc.Qt.AlignCenter)
                
        self.start_label = qtw.QLabel('Start Frame:', alignment=qtc.Qt.AlignCenter)
        self.start_value = qtw.QLabel('A', alignment=qtc.Qt.AlignCenter)
        self.end_label = qtw.QLabel('End Frame:', alignment=qtc.Qt.AlignCenter)
        self.end_value = qtw.QLabel('B', alignment=qtc.Qt.AlignCenter)
        
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
        vbox.addWidget(self.middle_widget, alignment=qtc.Qt.AlignCenter, stretch=1)
        vbox.addWidget(self.bottom_widget, alignment=qtc.Qt.AlignCenter)
        
        self.setLayout(vbox)
        self.setFixedWidth(300)
        self.__update__()

    def set_annotation(self, annotation):
        self.scheme = annotation.dataset.scheme
        self.__update__()

    def set_selected(self, sample):
        self.sample = sample
        self.__update__()
    
    def __update__(self):
        if self.sample is None:
            widget = qtw.QLabel('There is no sample to show yet.', alignment=qtc.Qt.AlignCenter)
            self.layout().replaceWidget(self.middle_widget, widget)
            self.middle_widget.setParent(None)
            self.middle_widget = widget
            self.start_value.setText(str(0))
            self.end_value.setText(str(0))
        
        # Case 2: Sample is not annotated yet
        elif not self.sample.annotation_exists:
            widget = qtw.QLabel('The sample is not annotated yet.', alignment=qtc.Qt.AlignCenter)
            self.layout().replaceWidget(self.middle_widget, widget)
            self.middle_widget.setParent(None)
            self.middle_widget = widget
            self.start_value.setText(str(self.sample.start_position))
            self.end_value.setText(str(self.sample.end_position))
        
        # Case 3: Sample and scheme loaded
        else: 
            widget = qtw.QWidget(self)
            widget.setLayout(qtw.QFormLayout())
            
            for group_name, group_elements in self.scheme:                
                scroll_area = qtw.QScrollArea(self)
                scroll_area.setFixedHeight(50)
                inner_widget = qtw.QWidget(scroll_area)
                inner_widget.setLayout(qtw.QVBoxLayout())
                inner_widget.layout().setAlignment(qtc.Qt.AlignCenter)
        
                for elem in group_elements:
                    if self.sample.annotation[group_name][elem] == 1:
                        lbl = qtw.QLabel(elem, alignment=qtc.Qt.AlignCenter)
                        lbl.setFixedWidth(150)
                        lbl.setAlignment(qtc.Qt.AlignCenter)
                        inner_widget.layout().addWidget(lbl, alignment=qtc.Qt.AlignCenter)
                
                scroll_area.setWidget(inner_widget)
                
                lbl = qtw.QLabel(group_name)
                lbl.setAlignment(qtc.Qt.AlignCenter)
                widget.layout().addRow(lbl, scroll_area)

            self.layout().replaceWidget(self.middle_widget, widget)
            self.middle_widget.setParent(None)
            self.middle_widget = widget
            self.start_value.setText(str(self.sample.start_position))
            self.end_value.setText(str(self.sample.end_position))

def clear_layout(widget):
    layout = widget.layout()
    for i in reversed(range(layout.count())): 
        layout.itemAt(i).widget().setParent(None)

    
if __name__ == "__main__":
    import sys
    app = qtw.QApplication(sys.argv)

    widget = QDisplaySample()
    
    import data_classes.sample as sample
    widget.set_sample(sample.Sample(0, 100, None))
    widget.set_sample(sample.Sample(50, 250, None))
    
    #widget.resize(400,300)
    widget.show()

    sys.exit(app.exec_())