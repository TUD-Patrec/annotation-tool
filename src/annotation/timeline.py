from collections import namedtuple
from typing import Tuple

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.data_model.sample import Sample
from src.settings import settings
from src.utility import functions
from src.utility.functions import FrameTimeMapper, ms_to_time_string

ScalingRatio = namedtuple("ScalingRatio", ["Frames", "Pixels"])


class Scaling:
    def __init__(self, parent: qtw.QWidget):
        self.idx = 0
        self.parent = parent
        self.negative_scales = [
            ScalingRatio(1, 2),
        ]
        self.positive_scales = [ScalingRatio(2**i, 1) for i in range(0, 64)]

    @property
    def width(self):
        return self.parent.width()

    @property
    def n_frames(self):
        return self.parent.n_frames

    @property
    def ratio(self) -> Tuple[int, int]:
        """
        Returns the scaling ratio for the timeline. The scaling ratio is the ratio between the number of pixels and the
        number of frames. For example, if the scaling ratio is 1, then each pixel represents one frame. If the scaling ratio
        is 2, then each pixel represents two frames.

        Returns:
            Tuple[int, int]: (pixels, frames)
        """

        if self.idx < 0:
            return self.negative_scales[self.idx]
        else:
            current = self.positive_scales[self.idx]

            max_ratio = self.n_frames / self.width

            if current.Frames / current.Pixels > max_ratio:
                return ScalingRatio(self.n_frames, self.width)
            else:
                return current

    @property
    def ratio_f(self) -> float:
        """
        Returns the scaling ratio as a float [Frames per pixel].

        Returns:
            float: The scaling ratio.
        """
        return self.ratio.Frames / self.ratio.Pixels

    def pixel_to_frame(self, x) -> int:
        """
        Converts a pixel position to a frame position.

        Args:
            x (int): The pixel position.

        Returns:
            int: The frame position.
        """
        M = self.width
        N = int(M * self.ratio_f)
        return functions.scale(M, N, x)[0]

    def frame_to_pixel(self, x) -> int:
        """
        Converts a frame position to a pixel position.

        Args:
            x (int): The frame position.

        Returns:
            int: The pixel position.
        """
        M = self.width
        N = int(M * self.ratio_f)
        return functions.scale(N, M, x)[0]

    def increase(self):
        """Zoom out."""
        if self.idx < len(self.positive_scales) - 1:
            current_ratio = self.ratio_f
            self.idx += 1
            new_ratio = self.ratio_f
            if new_ratio == current_ratio:
                self.idx -= 1
            print("increase", self.ratio_f)

    def decrease(self):
        """Zoom in."""
        if self.idx > -len(self.negative_scales):
            self.idx -= 1
            print("decrease", self.ratio_f)


class QTimeLine(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)

    def __init__(self):
        super(qtw.QWidget, self).__init__()
        self.frame_idx = 0
        self.pos = None  # Don't remove
        self.scaler = Scaling(self)
        self.n_frames = self.width()
        self.lower = 0

        self.samples = []
        self.current_sample = None

        # Set variables
        self.backgroundColor = qtg.QColor(60, 63, 65)
        self.textColor = qtg.QColor(187, 187, 187)
        self.font = qtg.QFont("Decorative", settings.font_size)
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
        self.update()

    def update_visible_range(self):
        if self.frame_idx <= self.scroll_left_interval[1]:
            too_less = self.scroll_left_interval[1] - self.frame_idx
            self.lower = max(self.lower - (too_less + 1), 0)
        elif self.frame_idx >= self.scroll_right_interval[0]:
            too_far = self.frame_idx - self.scroll_right_interval[0]
            self.lower += too_far + 1
        if self.upper > self.n_frames - 1:
            too_far = self.upper - (self.n_frames - 1)
            self.lower -= too_far
        self.check_consistency()

    def zoom_in(self):
        lo = self.lower
        hi = self.upper
        zoom_in_left_half = self.frame_idx - lo <= self.n_inner_frames / 2

        self.scaler.decrease()

        if zoom_in_left_half:
            self.lower = max(lo, self.frame_idx - self.n_inner_frames // 2)
        else:
            hi_tmp = min(hi, self.frame_idx + self.n_inner_frames // 2)
            self.lower = hi_tmp - self.scaler.pixel_to_frame(self.width()) + 1

        assert self.lower >= lo, f"{self.lower = }, {lo = }"
        assert self.upper <= hi, f"{self.upper} {hi}"
        self.update()

    def zoom_out(self):
        self.scaler.increase()
        self.lower = max(0, self.frame_idx - self.n_inner_frames // 2)
        if self.upper > self.n_frames - 1:
            too_far = self.upper - (self.n_frames - 1)
            self.lower -= too_far

        self.update()

    def check_consistency(self):
        assert self.lower >= 0, f"{self.lower = }"
        assert self.upper <= self.n_frames - 1, f"{self.upper = }, {self.n_frames = }"
        assert self.frame_idx >= self.lower
        assert self.upper <= self.n_frames - 1, f"{self.upper = } {self.n_frames = }"

    @qtc.pyqtSlot(int)
    def set_position(self, pos):
        assert 0 <= pos < self.n_frames
        self.frame_idx = pos
        self.update()

    @qtc.pyqtSlot(list, Sample)
    def set_samples(self, samples, selected_sample):
        self.samples = samples
        self.current_sample = selected_sample
        self.update()

    # mouse scroll event
    def wheelEvent(self, e):
        if self.is_in:
            # check if control key is pressed
            if e.modifiers() == qtc.Qt.ControlModifier:
                if e.angleDelta().y() > 0:
                    self.zoom_in()
                else:
                    self.zoom_out()
        else:
            e.ignore()

    def mouseMoveEvent(self, e):
        self.pos = e.pos()

        # if mouse is being pressed, update pointer
        if self.clicking:
            x = self.pos.x()
            x = max(0, x)
            x = min(x, self.width() - 1)

            self.frame_idx = self.scaler.pixel_to_frame(x) + self.lower
            self.position_changed.emit(self.frame_idx)

        self.update()

    def mousePressEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            x = e.pos().x()
            self.frame_idx = self.scaler.pixel_to_frame(x) + self.lower
            self.position_changed.emit(self.frame_idx)
            self.clicking = True  # Set clicking check to true

        self.update_visible_range()
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
        self.update()

    def update(self) -> None:
        self.update_visible_range()
        super().update()

    def paintEvent(self, event):
        # set some constants
        HEIGHT_SAMPLE = 70
        MARGIN_SAMPLE = 10
        WIDTH_TEXT = 100
        HEIGHT_TEXT = 25
        HEIGHT_LINE = 40
        HEIGHT_DASHED_LINE = 20
        MARGIN_HORIZONTAL_LINES = 40

        # step_size between ticks
        dist = 100

        qp = qtg.QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(qtg.QPainter.Antialiasing)

        # Draw time
        pos = dist
        while pos < self.width():
            frame_idx = self.scaler.pixel_to_frame(int(pos)) + self.lower

            time_stamp = FrameTimeMapper.instance().frame_to_ms(frame_idx)
            time_stamp = ms_to_time_string(time_stamp)
            time_stamp = time_stamp.split(":")
            time_stamp = ":".join(time_stamp[:-1])

            start_pos = int(pos) - WIDTH_TEXT // 2

            # Draw time_stamps and frame_numbers
            qp.drawText(
                start_pos,
                0,
                WIDTH_TEXT,
                HEIGHT_TEXT,
                qtc.Qt.AlignHCenter,
                str(frame_idx),
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
                time_stamp,
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

        # Draw pos
        if self.frame_idx is not None:
            pos = self.scaler.frame_to_pixel(self.frame_idx - self.lower)

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
            if sample.start_position > self.upper or sample.end_position < self.lower:
                continue

            sample_start = self.scaler.frame_to_pixel(
                sample.start_position - self.lower
            )
            sample_end = self.scaler.frame_to_pixel(sample.end_position - self.lower)
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

    @property
    def upper(self):
        return self.lower + self.scaler.pixel_to_frame(self.width()) - 1

    @property
    def visible_range(self):
        return self.lower, self.upper

    @property
    def n_inner_frames(self):
        return self.upper - self.lower + 1

    @property
    def scroll_left_interval(self):
        return self.lower, self.lower + self.n_inner_frames // 10

    @property
    def scroll_right_interval(self):
        return self.upper - self.n_inner_frames // 10, self.upper
