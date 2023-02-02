import PyQt6.QtWidgets as qtw
import numpy as np
import pyqtgraph as pg


class HistogramWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()

        # make the histogram look like a histogram
        self.getAxis("bottom").setStyle(showValues=False)
        self.getAxis("left").setStyle(showValues=False)
        self.getAxis("left").setTicks([])
        self.getAxis("bottom").setTicks([])
        self.showGrid(x=False, y=False)
        self.setMouseEnabled(x=False, y=False)
        self.setMenuEnabled(False)

        self.data = None
        self.position = None

        self.setFixedHeight(175)

    def reset(self) -> None:
        """Reset the histogram."""
        self.position = None
        self.data = None
        self.__plot__()

    def plot_data(self, data: np.ndarray = None, position: float = None) -> None:
        """Plot the data and the position on the histogram."""
        self.data = data
        self.position = position
        self.__plot__()

    def __plot__(self) -> None:
        """Plot the data and the position on the histogram."""
        self.clear()

        # color the background of the histogram
        app = qtw.QApplication.instance()
        self.setBackground(app.palette().window().color())

        if self.data is not None:  # if data is available
            y, x = np.histogram(self.data, bins=np.linspace(0, 1, 25), density=True)
            self.plotItem.plot(x, y, stepMode=True, fillLevel=0, brush=(0, 255, 0, 150))
            if self.position is not None:  # if position is available
                # draw thick red line at position
                self.plot(
                    [self.position, self.position],
                    [0, np.max(y)],
                    pen=pg.mkPen("r", width=1),
                )
