from dataclasses import dataclass, field
from typing import List

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

import sys


@dataclass(order=True)
class Sample:
    sort_index: int = field(init=False, repr=False)
    start_pos: int
    end_pos: int
    default_color: qtc.Qt.GlobalColor = qtc.Qt.lightGray
    color: qtc.Qt.GlobalColor = qtc.Qt.lightGray

    def __post_init__(self):
        self.sort_index = self.start_pos

    def get_n_frames(self):
        return self.end_pos - self.start_pos
    

class QTimeLine(qtw.QWidget):

    positionChanged = qtc.pyqtSignal(int)
    selectionChanged = qtc.pyqtSignal(Sample)

    def __init__(self):
        super(qtw.QWidget, self).__init__()
        # Position where the timeline starts (since its always aligned with the current frame position)
        self.current_frame_position = 0

        # List of ranges (start_frame, end_frame)
        # TODO KEEP SORTED -> allow binary search
        self.samples = []
        self.selected_sample = None 
        self.pointer_is_active = False

        # Set variables
        self.backgroundColor = qtg.QColor(60, 63, 65)
        self.textColor = qtg.QColor(187, 187, 187)
        self.font = qtg.QFont('Decorative', 10)
        self.pos = None
        self.pointer_pos = None
        self.clicking = False  # Check if mouse left button is being pressed
        self.is_in = False  # check if user is in the widget

        self.setMouseTracking(True)  # Mouse events
        self.setAutoFillBackground(True)  # background

        pal = qtg.QPalette()
        pal.setColor(qtg.QPalette.Background, self.backgroundColor)
        self.setPalette(pal)


    qtc.pyqtSlot(int)
    def set_position(self, pos):
        self.current_frame_position = pos
        self.update()


    qtc.pyqtSlot()
    def set_pointer_active(self):
        lower, _ = self.__get_range__()
        self.pointer_pos = self.current_frame_position - lower
        self.pointer_is_active = True 


    qtc.pyqtSlot()
    def set_pointer_inactive(self):
        self.pointer_is_active = False
    

    qtc.pyqtSlot(list)
    def set_samples(self, samples: List[Sample]):
        for elem in samples:
            assert isinstance(elem, Sample)
        self.samples = sorted(samples)


    def paintEvent(self, event):
        qp = qtg.QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(qtg.QPainter.Antialiasing)

        # get current shift
        lower, upper = self.__get_range__()


        # Draw time
        x_pixel_pos = 100

        while x_pixel_pos <= self.width():
            txt = str(lower + x_pixel_pos)
            qp.drawText(x_pixel_pos - 50, 0, 100, 100, qtc.Qt.AlignHCenter, txt)

            x_pixel_pos += 100

        # Draw down line
        qp.setPen(qtg.QPen(qtc.Qt.darkCyan, 5, qtc.Qt.SolidLine))
        qp.drawLine(0, 40, self.width(), 40)

        # Draw dash lines
        x_pixel_pos = 0
        qp.setPen(qtg.QPen(self.textColor))
        qp.drawLine(0, 40, self.width(), 40)
        while x_pixel_pos <= self.width():
            qp.drawLine(x_pixel_pos, 40, x_pixel_pos, 20)
            x_pixel_pos += 50

        if self.pos is not None and self.is_in:
            qp.drawLine(self.pos.x(), 0, self.pos.x(), 40)

        if self.pointer_pos is not None and self.pointer_is_active:
            pos = self.pointer_pos

            line = qtc.QLine(qtc.QPoint(pos, 40),
                         qtc.QPoint(pos, self.height()))
            poly = qtg.QPolygon([qtc.QPoint(pos - 10, 20),
                             qtc.QPoint(pos + 10, 20),
                             qtc.QPoint(pos, 40)])
        else:
            pos = self.current_frame_position - lower
            line = qtc.QLine(qtc.QPoint(pos, 40),
                         qtc.QPoint(pos, self.height()))
            poly = qtg.QPolygon([qtc.QPoint(pos - 10, 20),
                             qtc.QPoint(pos + 10, 20),
                             qtc.QPoint(pos, 40)])
            #line = qtc.QLine(qtc.QPoint(0, 0), qtc.QPoint(0, self.height()))
            #poly = qtg.QPolygon([qtc.QPoint(-10, 20), qtc.QPoint(10, 20), qtc.QPoint(0, 40)])

        # Draw samples
        for sample in self.__get_samples_in_range__():
            
            lower_end = max(lower, sample.start_pos) - lower
            # Clear clip path
            path = qtg.QPainterPath()
            path.addRect(qtc.QRectF(lower_end, 50, sample.get_n_frames(), 200))
            qp.setClipPath(path)

            # Draw sample
            path = qtg.QPainterPath()
            qp.setPen(sample.color)
            path.addRect(qtc.QRectF(lower_end, 50, sample.get_n_frames(), 50))
            qp.fillPath(path, sample.color)
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
        lower, upper = self.__get_range__()

        self.pos = e.pos()

        # if mouse is being pressed, update pointer
        if self.pointer_is_active and self.clicking:
            x = self.pos.x()
            self.pointer_pos = x
            self.positionChanged.emit(x + lower)
            self.checkSelection(x)

        self.update()


    # Mouse pressed
    def mousePressEvent(self, e):
        lower, upper = self.__get_range__()

        if self.pointer_is_active and e.button() == qtc.Qt.LeftButton:
            x = e.pos().x()
            self.pointer_pos = x
            self.positionChanged.emit(x + lower)

            self.checkSelection(x)

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


    # check selection
    def checkSelection(self, x):
        lower, _ = self.__get_range__()
        # Check if user clicked in video sample
        for sample in self.samples:
            #print(x, sample.start_pos, sample.end_pos)
            if sample.start_pos <= x + lower <= sample.end_pos:
                sample.color = qtc.Qt.darkCyan
                if self.selected_sample is not sample:
                    self.selected_sample = sample
                    self.selectionChanged.emit(sample)
            else:
                sample.color = sample.default_color


    # Get selected sample
    def get_selected_sample(self):
        return self.selected_sample


    def __get_range__(self):
        width = self.width()
        lower = max(0, self.current_frame_position - width // 2)
        upper = lower + width
        return lower, upper
    

# TODO Faster implementation
    def __get_samples_in_range__(self):
        return self.samples

    @qtc.pyqtSlot()
    def _load_examples_(self):
        smpls = [Sample(100,299), Sample(0, 99), Sample(600, 799), Sample(1000, 1500)]
        self.set_samples(smpls)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    MainWindow = QTimeLine()
    MainWindow.resize(400,300)

    MainWindow.set_pointer_active()
    MainWindow._load_examples_()
    MainWindow.set_position(100)
    MainWindow.positionChanged.connect(lambda x: print(x))

    #MainWindow.selectionChanged.connect(lambda x: print(x.n_frames))

    MainWindow.show()
    sys.exit(app.exec_())

