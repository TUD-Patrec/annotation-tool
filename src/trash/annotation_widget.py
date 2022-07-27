import sys
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

import numpy as np
from .util import util
from .sample import Sample

from typing import List


class QAnnotationManager(qtw.QWidget):
    selected_sample_changed = qtc.pyqtSignal(Sample)
    samples_changed = qtc.pyqtSignal(list)

    def __init__(self) -> None:
        super(qtw.QWidget, self).__init__()
        self.samples: List[Sample] = []
        self.selected_sample = None
        self.duration = 0
        
        self.annotation_scheme = None
        self.dependencies = None
        
        # layout
        vbox = qtw.QVBoxLayout(self)
        self.setLayout(vbox)


    @qtc.pyqtSlot(int)
    def set_duration(self, duration):
        assert duration >= self.duration

        if duration > self.duration:
            place_holder_sample = Sample(self.duration, duration - 1, self.__default_label__, np.copy(self.default_attribute_vector))
            self.samples.append(place_holder_sample)
            self.duration = duration
            self.samples_changed.emit(self.samples)

    def set_annotation_scheme(self, annotation_scheme):
        self.annotation_scheme = annotation_scheme
        
    def set_dependencies(self, dependencies):
        self.dependencies = dependencies

    @qtc.pyqtSlot(int)
    def check_for_selected_sample(self, frame_idx):
        cnt = 0
        for sample in self.samples:
            if sample.start_pos <= frame_idx <= sample.end_pos:
                cnt += 1
                if self.selected_sample != sample:
                    self.selected_sample = sample
                    self.selected_sample_changed.emit(sample)
        assert cnt < 2


    @qtc.pyqtSlot(int)
    def split_at_frame(self, frame_idx):
        assert 0 < frame_idx < self.duration - 1
        idx = 0 
        for sample in self.samples:
            if sample.start_pos < frame_idx <= sample.end_pos:
                start_1, end_1 = sample.start_pos, frame_idx-1
                start_2, end_2 = frame_idx, sample.end_pos

                s1 = Sample(start_1, end_1, sample.label, sample.attribute_vector)
                s2 = Sample(start_2, end_2, self.__default_label__, self.default_attribute_vector)

                self.samples.remove(sample)
                self.samples.insert(idx, s1)
                self.samples.insert(idx + 1, s2)

            idx += 1
                

    def merge_at_frame(self, frame_idx):
        pass
    
    





if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)

    anno_widget = QAnnotationManager()
    anno_widget.resize(400,300)
    anno_widget.show()

    anno_widget.display()

    anno_widget.load_lara_default()

    anno_widget.display()

    print(anno_widget.get_default_vector())

    anno_widget.update()
    
    
    

    sys.exit(app.exec_())
