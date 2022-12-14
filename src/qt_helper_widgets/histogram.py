import PyQt5.QtWidgets as qtw
import numpy as np
import pyqtgraph as pg


class HistogramWidget(qtw.QWidget):
    def __init__(self):
        super().__init__()

        self.layout = qtw.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.histogram = pg.PlotWidget(self)
        # make the histogram look like a histogram
        self.histogram.getAxis("bottom").setStyle(showValues=False)
        self.histogram.getAxis("left").setStyle(showValues=False)
        self.histogram.getAxis("left").setTicks([])
        self.histogram.getAxis("bottom").setTicks([])
        self.histogram.showGrid(x=False, y=False)
        self.histogram.setMouseEnabled(x=False, y=False)
        self.histogram.setMenuEnabled(False)

        self.layout().addWidget(self.histogram)
        self.data = None
        self.position = None

        self.setFixedHeight(175)

    def reset(self) -> None:
        """Reset the histogram."""
        self.position = None
        self.data = None
        self.__plot__()

    def plot(self, data: np.ndarray = None, position: float = None) -> None:
        """Plot the data and the position on the histogram."""
        self.data = data
        self.position = position
        self.__plot__()

    def __plot__(self) -> None:
        """Plot the data and the position on the histogram."""
        self.histogram.clear()

        # color the background of the histogram
        self.histogram.setBackground(self.palette().window().color())

        if self.data is not None:  # if data is available
            y, x = np.histogram(self.data, bins=np.linspace(0, 1, 25), density=True)
            self.histogram.plotItem.plot(
                x, y, stepMode=True, fillLevel=0, brush=(0, 255, 0, 150)
            )
            if self.position is not None:  # if position is available
                # draw thick red line at position
                self.histogram.plot(
                    [self.position, self.position],
                    [0, np.max(y)],
                    pen=pg.mkPen("r", width=2),
                )
