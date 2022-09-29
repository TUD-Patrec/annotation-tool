import matplotlib.pyplot as plt
import numpy as np
import PyQt5.QtWidgets as qtw

from matplotlib.backends.backend_qt import FigureCanvasQT as FigureCanvas


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
        return isinstance(self.data, np.ndarray) and isinstance(self.position, int)

    def plot(self):
        self.figure.clear()
        if self.plot_possible():
            plt.axvline(x=self.position, color='r', label='')
            plt.hist(self.data, bins=20)
            self.canvas.draw()
