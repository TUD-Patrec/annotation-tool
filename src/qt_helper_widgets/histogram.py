import PyQt5.QtWidgets as qtw
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Qt5Agg")


fig = plt.figure(figsize=(8, 6), dpi=80)  # create a figure object


class HistogramWidget(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(HistogramWidget, self).__init__(*args, **kwargs)

        self.position = 0
        self.data = None
        self.current_color = None

        self.figure = fig

        # canvas Widget that displays the fig
        self.canvas = FigureCanvas(self.figure)

        # layout
        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

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
        self.figure.clear()  # clear the figure
        color = (
            self.palette().window().color().name()
        )  # get the background color of the widget
        if (
            self.current_color is None or color != self.current_color
        ):  # if the color has changed
            ax = plt.axes()
            ax.set_facecolor(color)
            self.figure.set_facecolor(color)
        if self.data is not None:  # if data is available
            if self.position is not None:  # if position is available
                plt.axvline(x=self.position, color="r", label="")

            plt.hist(self.data, range=(0, 1), bins=25, density=True, facecolor="g")
            plt.yticks([])
            plt.xticks([0, 1], [0, 1])
        else:
            plt.text(
                0.5,
                0.5,
                "No data available",
                horizontalalignment="center",
                verticalalignment="center",
            )
            plt.yticks([])
            plt.xticks([])
        plt.box(False)  # remove the box around the plot
        self.canvas.draw()  # draw the plot
