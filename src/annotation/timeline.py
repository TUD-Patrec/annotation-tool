import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.dataclasses.sample import Sample
from src.utility import functions
from src.utility.functions import FrameTimeMapper, ms_to_time_string


class QTimeLine(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)

    def __init__(self):
        super(qtw.QWidget, self).__init__()
        self.pointer_position = 0
        self.pos = None  # Dont remove
        self.n_frames = self.width()

        self._frame_to_pixel, self._pixel_to_frame = functions.scale_functions(
            N=self.n_frames, M=self.width(), last_to_last=True
        )

        self.samples = []
        self.current_sample = None

        # Set variables
        self.backgroundColor = qtg.QColor(60, 63, 65)
        self.textColor = qtg.QColor(187, 187, 187)
        self.font = qtg.QFont("Decorative", 10)
        self.clicking = False  # Check if mouse left button is being pressed
        self.is_in = False  # check if user is in the widget

        self.setMouseTracking(True)  # Mouse events
        self.setAutoFillBackground(True)  # background

        # Constants
        self.setMinimumHeight(200)

    @qtc.pyqtSlot(int)
    def set_range(self, n):
        assert 0 < n
        self.n_frames = n
        self._frame_to_pixel, self._pixel_to_frame = functions.scale_functions(
            N=self.n_frames, M=self.size().width(), last_to_last=True
        )
        self.update()

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        assert 0 <= pos < self.n_frames
        pixel_pos, _ = self._frame_to_pixel(pos)
        self.pointer_position = pixel_pos
        self.update()

    @qtc.pyqtSlot(list, Sample)
    def set_samples(self, samples, selected_sample):
        self.samples = samples
        self.current_sample = selected_sample
        self.update()

    def mouseMoveEvent(self, e):
        self.pos = e.pos()

        # if mouse is being pressed, update pointer
        if self.clicking:
            x = self.pos.x()
            x = max(0, x)
            x = min(x, self.width() - 1)

            self.pointer_position = x
            frame_position = self._pixel_to_frame(x)[0]
            self.position_changed.emit(frame_position)

        self.update()

    def mousePressEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            x = e.pos().x()
            self.pointer_position = x
            frame_position = self._pixel_to_frame(x)[0]
            self.position_changed.emit(frame_position)

            self.clicking = True  # Set clicking check to true

        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            self.clicking = False  # Set clicking check to false

    def enterEvent(self, e):
        self.is_in = True

    def leaveEvent(self, e):
        self.is_in = False
        self.update()

    def resizeEvent(self, event: qtg.QResizeEvent) -> None:
        qtw.QWidget.resizeEvent(self, event)
        super().resizeEvent(event)

        # adjust pointer_position -> first map to frame-space
        # by averaging both bounds of the mapping we get the 'best' conversion
        pointer_pos = (
            self._pixel_to_frame(self.pointer_position)[0]
            + self._pixel_to_frame(self.pointer_position)[1]
        ) // 2

        self._frame_to_pixel, self._pixel_to_frame = functions.scale_functions(
            N=self.n_frames, M=event.size().width(), last_to_last=True
        )

        # adjust pointer_position -> after updating the size: map back to pixel-space
        # by averaging both bounds of the mapping we get the 'best' conversion
        self.pointer_position = (
            self._frame_to_pixel(pointer_pos)[0] + self._frame_to_pixel(pointer_pos)[1]
        ) // 2

        self.update()

    def paintEvent(self, event):
        # set some constants
        N_TICKS = 15
        HEIGHT_SAMPLE = 70
        MARGIN_SAMPLE = 10
        WIDTH_TEXT = 100
        HEIGHT_TEXT = 25
        HEIGHT_LINE = 40
        HEIGHT_DASHED_LINE = 20
        MARGIN_HORIZONTAL_LINES = 40

        # step_size between ticks
        dist = self.width() / (N_TICKS + 1)

        qp = qtg.QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(qtg.QPainter.Antialiasing)

        # Draw time
        pos = dist
        while pos < self.width() - int(dist):
            frame_idx = self._pixel_to_frame(int(pos))[0]

            time_stamp = FrameTimeMapper.instance().frame_to_ms(frame_idx)
            time_stamp = ms_to_time_string(time_stamp)

            start_pos = int(pos) - WIDTH_TEXT // 2

            # Draw time_stamps and frame_numbers
            qp.drawText(
                start_pos, 0, WIDTH_TEXT, HEIGHT_TEXT, qtc.Qt.AlignHCenter, time_stamp
            )
            lower_text_y = (
                MARGIN_HORIZONTAL_LINES
                + 2 * MARGIN_SAMPLE
                + HEIGHT_SAMPLE
                + HEIGHT_TEXT
            )
            qp.drawText(
                start_pos,
                lower_text_y,
                WIDTH_TEXT,
                HEIGHT_TEXT,
                qtc.Qt.AlignHCenter,
                str(frame_idx),
            )

            pos += dist

        # Draw horizontal lines
        qp.setPen(qtg.QPen(qtc.Qt.darkCyan, 5, qtc.Qt.SolidLine))
        qp.drawLine(0, MARGIN_HORIZONTAL_LINES, self.width(), 40)
        lower_horizontal_line_y = (
            MARGIN_HORIZONTAL_LINES + 2 * MARGIN_SAMPLE + HEIGHT_SAMPLE
        )
        qp.drawLine(0, lower_horizontal_line_y, self.width(), lower_horizontal_line_y)

        # Draw dash lines
        qp.setPen(qtg.QPen(self.textColor))
        pos = dist
        while pos < self.width():
            qp.drawLine(int(pos), MARGIN_HORIZONTAL_LINES, int(pos), HEIGHT_DASHED_LINE)
            lower_dashed_line_y = (
                MARGIN_HORIZONTAL_LINES + 2 * MARGIN_SAMPLE + HEIGHT_SAMPLE
            )
            qp.drawLine(
                int(pos),
                lower_dashed_line_y,
                int(pos),
                lower_dashed_line_y + HEIGHT_DASHED_LINE,
            )
            pos += dist

        # Draw line of current mouse-position
        if self.pos is not None and self.is_in:
            # qp.drawLine(self.pos.x(), 0, self.pos.x(), HEIGHT_LINE)
            line_height = MARGIN_HORIZONTAL_LINES + 2 * MARGIN_SAMPLE + HEIGHT_SAMPLE
            qp.drawLine(self.pos.x(), 0, self.pos.x(), line_height + HEIGHT_LINE)

        # Draw pointer_position
        if self.pointer_position is not None:
            pos = self.pointer_position

            line_height = 2 * MARGIN_SAMPLE + HEIGHT_SAMPLE
            line = qtc.QLine(
                qtc.QPoint(pos, MARGIN_HORIZONTAL_LINES),
                qtc.QPoint(pos, MARGIN_HORIZONTAL_LINES + line_height),
            )
            poly = qtg.QPolygon(
                [
                    qtc.QPoint(pos - 10, 20),
                    qtc.QPoint(pos + 10, 20),
                    qtc.QPoint(pos, 40),
                ]
            )
        else:
            pos = 0
            line = qtc.QLine(qtc.QPoint(pos, 40), qtc.QPoint(pos, self.height()))
            poly = qtg.QPolygon(
                [
                    qtc.QPoint(pos - 10, 20),
                    qtc.QPoint(pos + 10, 20),
                    qtc.QPoint(pos, 40),
                ]
            )

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
                color = qtg.QColor(r, g, b, 255)

            # Clear clip path
            height = MARGIN_HORIZONTAL_LINES + MARGIN_SAMPLE

            path = qtg.QPainterPath()
            path.addRoundedRect(
                qtc.QRectF(sample_start, height, sample_length, HEIGHT_SAMPLE), 10, 10
            )
            qp.setClipPath(path)

            path = qtg.QPainterPath()
            qp.setPen(color)
            path.addRoundedRect(
                qtc.QRectF(sample_start, height, sample_length, HEIGHT_SAMPLE), 10, 10
            )
            qp.fillPath(path, color)
            qp.drawPath(path)

        # Clear clip path
        path = qtg.QPainterPath()
        path.addRect(
            self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height()
        )
        qp.setClipPath(path)

        # Draw pointer
        qp.setPen(qtc.Qt.darkCyan)
        qp.setBrush(qtg.QBrush(qtc.Qt.darkCyan))

        qp.drawPolygon(poly)
        qp.drawLine(line)
        qp.end()
