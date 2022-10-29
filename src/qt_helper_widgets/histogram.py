import PyQt5.QtWidgets as qtw
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Qt5Agg")


class HistogramWidget(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(HistogramWidget, self).__init__(*args, **kwargs)

        self.position = 0
        self.data = None
        self.current_color = None

        # figure to plot on
        self.figure = plt.figure(figsize=(8, 6), dpi=80)

        # canvas Widget that displays the fig
        self.canvas = FigureCanvas(self.figure)

        # layout
        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

        self.setFixedHeight(175)

    def reset(self):
        self.position = 0
        self.data = None
        self.plot()

    def update_position(self, new_pos):
        self.position = new_pos
        self.plot()

    def update_data(self, data):
        self.data = data
        self.plot()

    def plot_data(self, data, position):
        self.data = data
        self.position = position
        self.plot()

    def plot_possible(self):
        return isinstance(self.data, np.ndarray) and isinstance(
            self.position, (float, int)
        )

    def plot(self):
        self.figure.clear()
        color = self.palette().window().color().name()
        if self.current_color is None or color != self.current_color:
            ax = plt.axes()
            ax.set_facecolor(color)
            self.figure.set_facecolor(color)
        if self.plot_possible():
            data = self.data
            position = self.position

            plt.axvline(x=position, color="r", label="")
            plt.hist(data, range=(0, 1), bins=25, density=True, facecolor="g")
            plt.yticks([])
            plt.xticks([0, 1], [0, 1])
        else:
            plt.yticks([])
            plt.xticks([])
        plt.box(False)
        self.canvas.draw()
