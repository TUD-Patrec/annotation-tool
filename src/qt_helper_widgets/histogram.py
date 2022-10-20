import PyQt5.QtWidgets as qtw
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Qt5Agg")


class Histogram_Widget(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(Histogram_Widget, self).__init__(*args, **kwargs)

        self.position = 0
        self.data = None

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        self.canvas = FigureCanvas(self.figure)

        # set the layout
        layout = qtw.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.setFixedHeight(200)

    def reset(self):
        self.position = 0
        self.data = None
        self.figure.clear()

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
        if self.plot_possible():
            data = self.data
            position = self.position

            plt.axvline(x=position, color="r", label="")
            # plt.hist(data, bins=25)
            plt.hist(data, range=(0, np.max(data)), bins=25)
            self.canvas.draw()

    def norm_to_percentage(self, x):
        lower, upper = np.min(self.data), np.max(self.data)
        res = 100 * (x - lower) / (upper - lower)
        return np.array(res, dtype=np.int64) if isinstance(x, np.ndarray) else int(res)
