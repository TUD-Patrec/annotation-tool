from collections import namedtuple
from typing import Tuple

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.data_model.sample import Sample
from src.settings import settings
from src.utility import functions

ScalingRatio = namedtuple("ScalingRatio", ["Frames", "Pixels"])


class Scaling:
    def __init__(self, parent: qtw.QWidget):
        self.idx = 0
        self.parent = parent
        self.negative_scales = [
            ScalingRatio(1, 8),
            ScalingRatio(1, 4),
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
        N = max(self.ratio.Pixels - 1, 0)
        M = max(
            self.ratio.Frames - 1, 0
        )  # -1 because we want to map the last pixel to the last frame
        return functions.scale(N, M, x)[0]

    def frame_to_pixel(self, x) -> int:
        """
        Converts a frame position to a pixel position.

        Args:
            x (int): The frame position.

        Returns:
            int: The pixel position.
        """
        N = max(self.ratio.Frames - 1, 0)
        M = max(
            self.ratio.Pixels - 1, 0
        )  # -1 because we want to map the last frame to the last pixel
        return functions.scale(N, M, x)[0]

    def increase(self):
        if self.idx < len(self.positive_scales) - 1:
            current_ratio = self.ratio_f
            self.idx += 1
            new_ratio = self.ratio_f
            if new_ratio == current_ratio:
                self.idx -= 1
            print("increase", self.ratio_f)

    def decrease(self):
        if self.idx > -len(self.negative_scales):
            self.idx -= 1
            print("decrease", self.ratio_f)


"""
class TestParent:
    def __init__(self):
        self.w = 1080
        self.n_frames = 24000

    def width(self):
        return self.w


s = Scaling(TestParent())
for _ in range(20):
    print(s.idx, s.ratio, s.ratio_f)
    print(s.frame_to_pixel(1079), s.pixel_to_frame(23999))
    print()
    s.increase()
"""


class QTimeLine(qtw.QWidget):
    position_changed = qtc.pyqtSignal(int)

    def __init__(self):
        super(qtw.QWidget, self).__init__()
        self.frame_idx = 0
        self.pointer_position = None  # Don't remove
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
        pixel_pos = self.scaler.frame_to_pixel(self.frame_idx)
        w = self.width()
        if pixel_pos is not None:
            # check if scroll is needed
            if pixel_pos <= 0:
                # scroll left
                self.lower = max(0, self.frame_idx - 1)
            elif pixel_pos >= w - 1:
                # scroll right
                upper = self.frame_idx + 1
                self.lower = max(0, upper - w + 1)

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
            if e.angleDelta().y() < 0:
                self.scaler.increase()
            else:
                self.scaler.decrease()
            self.update()
        else:
            e.ignore()

    def mouseMoveEvent(self, e):
        self.pointer_position = e.pos()

        # if mouse is being pressed, update pointer
        if self.clicking:
            x = self.pointer_position.x()
            x = max(0, x)
            x = min(x, self.width() - 1)

            self.frame_idx = self.scaler.pixel_to_frame(x) + self.lower
            self.position_changed.emit(self.frame_idx)

        # self.update()

    def mousePressEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            x = e.pos().x()
            self.frame_idx = self.scaler.pixel_to_frame(x) + self.lower
            self.position_changed.emit(self.frame_idx)
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
        self.update()

    def update(self) -> None:
        self.update_visible_range()
        super().update()

    def paintEvent(self, event):
        relative_frame_idx = self.frame_idx - self.lower
        pointer_x = self.scaler.frame_to_pixel(relative_frame_idx)
        print(
            f"frame_idx = {self.frame_idx}, rel_frame_idx = {relative_frame_idx}, pointer = {pointer_x}, visible = {self.visible_range}"
        )

        qp = qtg.QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(qtg.QPainter.Antialiasing)

        # Draw line of current mouse-position
        if self.pointer_position is not None and self.is_in:
            line_height = 40
            qp.drawLine(
                pointer_x,
                0,
                pointer_x,
                line_height,
            )

        # Draw pointer_position
        pos = (
            self.scaler.frame_to_pixel(self.frame_idx)
            if self.frame_idx is not None
            else 0
        )

        line = qtc.QLine(
            qtc.QPoint(pos, 40),
            qtc.QPoint(pos, self.height()),
        )
        poly = qtg.QPolygon(
            [
                qtc.QPoint(pos - 10, 20),
                qtc.QPoint(pos + 10, 20),
                qtc.QPoint(pos, 40),
            ]
        )

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
        lo = self.lower
        hi = lo + self.scaler.pixel_to_frame(self.width())
        return hi

    @property
    def visible_range(self):
        return self.lower, self.upper
