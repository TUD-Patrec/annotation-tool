import sys
import logging
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
from copy import deepcopy

from .data_classes.annotation import Annotation
from .data_classes.singletons import ColorMapper
from .utility.functions import FrameTimeMapper
from .data_classes.sample import Sample
from .dialogs.annotation_dialog import QAnnotationDialog
from .data_classes.singletons import Settings
from .utility import functions


class QAnnotationWidget(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)
    samples_changed = qtc.pyqtSignal(list, Sample)
    interrupt_replay = qtc.pyqtSignal()
    update_label = qtc.pyqtSignal(int, int)
    
    def __init__(self, *args, **kwargs):
        super(QAnnotationWidget, self).__init__(*args, **kwargs)
        self.samples = []
        self.sample_idx = 0
        self.position = 0
        self.n_frames = 0
        
        self.dataset_scheme = None
        self.dataset_dependencies = None
        
        self._show_ms = Settings.instance().show_millisecs
        
        self.undo_stack = list()
        self.redo_stack = list()
        
        self.annotate_btn = qtw.QAction('Annotate', self)
        self.annotate_btn.setStatusTip('Open the Annotation-Dialog for the highlighted sample.')
        self.annotate_btn.triggered.connect(lambda _: self.annotate_selected_sample())
        
        self.cut_btn = qtw.QAction('Cut', self)
        self.cut_btn.setStatusTip('Split the highlighted sample into two pieces.')
        self.cut_btn.triggered.connect(lambda _: self.split_selected_sample())
        
        self.cut_and_annotate_btn = qtw.QAction('C+A', self)
        self.cut_and_annotate_btn.setStatusTip('Cut and immediately annotate the current sample.')
        self.cut_and_annotate_btn.triggered.connect(lambda _: self.cut_and_annotate())
        
        self.merge_left_btn = qtw.QAction('Merge Left', self)
        self.merge_left_btn.setStatusTip('Merge highlighted sample with the left neighbour.')
        self.merge_left_btn.triggered.connect(lambda _: self.merge_samples(left=True))
        
        self.merge_right_btn = qtw.QAction('Merge Right', self)
        self.merge_right_btn.setStatusTip('Merge highlighted sample with the right neighbour')
        self.merge_right_btn.triggered.connect(lambda _: self.merge_samples(left=False))
       
        
        self.toolbar = qtw.QToolBar('Tools', self)
        self.toolbar.setOrientation(qtc.Qt.Vertical)

        self.toolbar.addAction(self.annotate_btn)
        self.toolbar.addAction(self.cut_btn)
        self.toolbar.addAction(self.cut_and_annotate_btn)
        self.toolbar.addAction(self.merge_left_btn)
        self.toolbar.addAction(self.merge_right_btn)
                
        # layout
        grid = qtw.QGridLayout(self)
        
        self.timeline = QTimeLine()
        self.timeline.position_changed.connect(lambda x: self.set_position(x, False))       # Update own position
        self.timeline.position_changed.connect(self.position_changed)                       # Notify listeners
        self.samples_changed.connect(self.timeline.set_samples)

        # grid.addWidget(self.lbl, 0, 0)
        grid.addWidget(self.toolbar, 0, 0)
        grid.addWidget(self.timeline, 0, 1, 2, 1)

        self.setLayout(grid)

    def is_loaded(self):
        return len(self.samples) > 0
    
    # TODO Maybe more fancy with functool.partial
    @qtc.pyqtSlot(int)
    def set_position(self, new_pos, update_timeline=True):
        if self.is_loaded() and self.position != new_pos:
            self.position = new_pos
            self.__update_label__()
            self.check_for_selected_sample()
            if update_timeline:
                self.timeline.set_position(new_pos)
            
    # TODO try get rid of self.n_frames -> apply set_position partially?
    @qtc.pyqtSlot(Annotation)
    def set_annotation(self, annotation):
        self.clear_undo_redo()
        if annotation is not None:
            self.samples = annotation.samples
            self.n_frames = annotation.frames
            self.timeline.set_range(annotation.frames)
            
            self.dataset_scheme = annotation.dataset.scheme
            self.dataset_dependencies = annotation.dataset.dependencies
            
            # Maybe somewhere else?
            color_mapper = ColorMapper.instance()
            color_mapper.scheme = annotation.dataset.scheme
            
            self.position = 0
            self.timeline.set_position(0)
            
            self.timeline.update()
            self.__update_label__()
            self.check_for_selected_sample(force_update=True)
        else:
            raise RuntimeError('annotation cant be None!')
    
    def settings_changed(self):
        self.__update_label__()
        self.timeline.update()
    
    def __update_label__(self):
        self.update_label.emit(self.position, self.n_frames)
    
    @qtc.pyqtSlot(int)
    def check_for_selected_sample(self, force_update=False):
        if self.is_loaded():
            for idx, sample in enumerate(self.samples):
                if sample.start_position <= self.position <= sample.end_position:
                    
                    # Case 1: Not initialized
                    if self.sample_idx is None:
                        selected_sample = None
                    # Case 2: Edge-Case, merged the last two samples
                    elif self.sample_idx >= len(self.samples):
                        selected_sample = None
                    # Case 3: Normal-Case
                    else:
                        selected_sample = self.samples[self.sample_idx]
                    
                    if force_update or selected_sample != sample:
                        self.sample_idx = idx
                        self.samples_changed.emit(self.samples, sample)
                    break

    def selected_sample(self):
        return self.samples[self.sample_idx]
    
    @qtc.pyqtSlot()
    def cut_and_annotate(self):
        self.split_selected_sample()
        self.annotate_selected_sample()
        
    @qtc.pyqtSlot()
    def annotate_selected_sample(self):
        if self.is_loaded():
            self.interrupt_replay.emit()
            if self.dataset_scheme is None:
                logging.warning('No Annotation Scheme loaded!')
                return

            sample = self.selected_sample()
            
            dialog = QAnnotationDialog(self.dataset_scheme, self.dataset_dependencies)
            
            dialog.new_annotation.connect(lambda x: self.update_sample_annotation(sample, x))
            dialog.open()
            if sample.annotation_exists:
                dialog._set_annotation(sample.annotation)
            dialog.exec_()
    
    def update_sample_annotation(self, sample, new_annotation):
        self.add_to_undo_stack()
        sample.annotation = new_annotation
        self.check_for_selected_sample(force_update=True)
        
    @qtc.pyqtSlot()
    def split_selected_sample(self):
        if self.is_loaded():
            sample = self.selected_sample()
            
            if sample.start_position < self.position:
                start_1, end_1 = sample.start_position, self.position
                start_2, end_2 = self.position + 1, sample.end_position

                s1 = Sample(start_1, end_1, sample.annotation)
                s2 = Sample(start_2, end_2, sample.annotation)
                
                self.add_to_undo_stack() 

                self.samples.remove(sample)
                self.samples.insert(self.sample_idx, s1)
                self.samples.insert(self.sample_idx + 1, s2)
                
                self.check_for_selected_sample(force_update=True)
            else:
                logging.warning('Cant split at first frame of a sample!')
        
    @qtc.pyqtSlot(bool)
    def merge_samples(self, left=True):
        if self.is_loaded():
            sample = self.samples[self.sample_idx]
            
            other_idx = self.sample_idx -1 if left else self.sample_idx + 1
            if 0 <= other_idx < len(self.samples):            
                other_sample = self.samples[other_idx]
            else:
                logging.warning('No sample to merge with!')
                return
                        
            start_idx, end_idx = min(sample.start_position, other_sample.start_position), max(sample.end_position, other_sample.end_position)
            
            merged_sample = Sample(start_idx, end_idx, sample.annotation)
            
            self.add_to_undo_stack()

            self.samples.remove(sample)
            self.samples.remove(other_sample)
            self.samples.insert(min(self.sample_idx, other_idx), merged_sample)

            self.check_for_selected_sample(force_update=True)
    
    def add_to_undo_stack(self):
        current_samples = deepcopy(self.samples)
        
        self.redo_stack = []            # clearing redo_stack
        self.undo_stack.append(current_samples)
        
        
        while len(self.undo_stack) > 20:
            self.undo_stack.pop(0)
        
        logging.info('undo_stack = {}'.format(len(self.undo_stack)))
    
    def undo(self):
        if len(self.undo_stack) >= 1:
            current_samples = deepcopy(self.samples)
            self.redo_stack.append(current_samples)
            
            self.samples = self.undo_stack.pop()
            self.check_for_selected_sample(force_update=True)
    
    def redo(self):
        if len(self.redo_stack) >= 1:
            current_samples = deepcopy(self.samples)
            self.undo_stack.append(current_samples)
            
            self.samples = self.redo_stack.pop()
            self.check_for_selected_sample(force_update=True)

    def clear_undo_redo(self):
        self.undo_stack = []
        self.redo_stack = []


class QTimeLine(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)

    def __init__(self):
        super(qtw.QWidget, self).__init__()          
        self.pointer_position = 0
        self.pos = None # Dont remove
        self.n_frames = self.width()
    
        self._frame_to_pixel, self._pixel_to_frame = functions.scale_functions(N=self.n_frames, M=self.width(), last_to_last=True)

        self.samples = []
        self.current_sample = None

        # Set variables
        self.backgroundColor = qtg.QColor(60, 63, 65)
        self.textColor = qtg.QColor(187, 187, 187)
        self.font = qtg.QFont('Decorative', 10)
        self.clicking = False                               # Check if mouse left button is being pressed
        self.is_in = False                                  # check if user is in the widget

        self.setMouseTracking(True)                         # Mouse events
        self.setAutoFillBackground(True)                    # background

        pal = qtg.QPalette()
        pal.setColor(qtg.QPalette.Background, self.backgroundColor)
        self.setPalette(pal)

        self.adjustSize()
    
    @qtc.pyqtSlot(int)
    def set_range(self, n):
        self.n_frames = n
        self._frame_to_pixel, self._pixel_to_frame = functions.scale_functions(N=self.n_frames, M=self.width(), last_to_last=True)
        self.update()

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        pixel_pos = self._frame_to_pixel(pos)[0]
        if pixel_pos != self.pointer_position:
            self.pointer_position = pixel_pos
            self.update()
 
    @qtc.pyqtSlot(list, Sample)
    def set_samples(self, samples, selected_sample):
        self.samples = samples
        self.current_sample = selected_sample
        self.update()
   
    def paintEvent(self, event):
        qp = qtg.QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(qtg.QPainter.Antialiasing)

        # Draw time
        
        n_ticks = 15
        dist = self.width() / (n_ticks+1)
                
        pos = dist
        while pos < self.width() - int(dist):
            frame_idx = self._pixel_to_frame(int(pos))[0]
            
            txt = FrameTimeMapper.instance().frame_repr(frame_idx)
            
            qp.drawText(int(pos)-50, 0, 100, 100, qtc.Qt.AlignHCenter, txt)
            pos += dist

        # Draw down line
        qp.setPen(qtg.QPen(qtc.Qt.darkCyan, 5, qtc.Qt.SolidLine))
        qp.drawLine(0, 40, self.width(), 40)

        # Draw dash lines
        qp.setPen(qtg.QPen(self.textColor))
        pos = dist
        while pos < self.width():
            qp.drawLine(int(pos), 40, int(pos), 20)
            pos += dist

        if self.pos is not None and self.is_in:
            try:
                qp.drawLine(self.pos.x(), 0, self.pos.x(), 40)
            except:
                logging.error('POS = {}'.format(self.pos()))
                raise RuntimeError()

        if self.pointer_position is not None:
            pos = self.pointer_position

            line = qtc.QLine(qtc.QPoint(pos, 40),
                         qtc.QPoint(pos, self.height()))
            poly = qtg.QPolygon([qtc.QPoint(pos - 10, 20),
                             qtc.QPoint(pos + 10, 20),
                             qtc.QPoint(pos, 40)])
        else:
            pos = 0
            line = qtc.QLine(qtc.QPoint(pos, 40),
                         qtc.QPoint(pos, self.height()))
            poly = qtg.QPolygon([qtc.QPoint(pos - 10, 20),
                             qtc.QPoint(pos + 10, 20),
                             qtc.QPoint(pos, 40)])

        # Draw samples
        for sample in self.samples:
            sample_start = self._frame_to_pixel(sample.start_position)[0]
            sample_end = self._frame_to_pixel(sample.end_position)[1]
            sample_length = sample_end - sample_start + 1
            
            if sample != self.current_sample:
                color = sample.color
            else:
                r = sample.color.red()
                g = sample.color.green()
                b = sample.color.blue()
                color = qtg.QColor(r,g,b, 255)
        
            # Clear clip path
            path = qtg.QPainterPath()
            path.addRoundedRect(qtc.QRectF(sample_start, 50, sample_length, 200), 10, 10)
            qp.setClipPath(path)

            path = qtg.QPainterPath()
            qp.setPen(color)
            path.addRoundedRect(qtc.QRectF(sample_start, 50, sample_length, 200), 10, 10)
            qp.fillPath(path, color)
            qp.drawPath(path)

        # Clear clip path
        path = qtg.QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        qp.setClipPath(path)

        # Draw pointer
        qp.setPen(qtc.Qt.darkCyan)
        qp.setBrush(qtg.QBrush(qtc.Qt.darkCyan))

        qp.drawPolygon(poly)
        qp.drawLine(line)
        qp.end()
   
    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()

        # if mouse is being pressed, update pointer
        if self.clicking:
            x = self.pos.x()
            x = max(0, x)
            x = min(x, self.width()-1)
            self.pointer_position = x
            
            frame_position = self._pixel_to_frame(x)[0]
            self.position_changed.emit(frame_position)

        self.update()

    # Mouse pressed
    def mousePressEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            x = e.pos().x()
            self.pointer_position = x
            frame_position = self._pixel_to_frame(x)[0]
            self.position_changed.emit(frame_position)
            
            self.clicking = True  # Set clicking check to true
        
        self.update()

    # Mouse release
    def mouseReleaseEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            self.clicking = False  # Set clicking check to false

    # Enter
    def enterEvent(self, e):
        self.is_in = True

    # Leave
    def leaveEvent(self, e):
        self.is_in = False
        self.update()

    def resizeEvent(self, event: qtg.QResizeEvent) -> None:
        qtw.QWidget.resizeEvent(self, event)
        super().resizeEvent(event)
        self._frame_to_pixel, self._pixel_to_frame = functions.scale_functions(N=self.n_frames, M=event.size().width(), last_to_last=True)
        self.update()

    
if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    MainWindow = QAnnotationWidget()
    MainWindow.resize(400,300)
    MainWindow.show()
    sys.exit(app.exec_())
