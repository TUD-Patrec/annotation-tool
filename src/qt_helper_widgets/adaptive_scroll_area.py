import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class QAdaptiveScrollArea(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.initUI()

    def initUI(self):
        self.layout = qtw.QHBoxLayout(self)
        self.scrollArea = qtw.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = qtw.QWidget()
        self.vBoxLayout = qtw.QVBoxLayout(self.scrollAreaWidgetContents)
        self.vBoxLayout.setAlignment(qtc.Qt.AlignLeft)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        # self.scrollArea.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)

        for item in self.items:
            self.vBoxLayout.addWidget(item)

    def updateUI(self):
        for item in self.items:
            item.setParent(self)

        self.scrollAreaWidgetContents = qtw.QWidget()
        self.vBoxLayout = qtw.QVBoxLayout(self.scrollAreaWidgetContents)
        self.vBoxLayout.setAlignment(qtc.Qt.AlignLeft)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        for item in self.items:
            self.vBoxLayout.addWidget(item)

    def clear(self):
        for item in self.items:
            item.setParent(None)
        self.items = []
        self.updateUI()

    def addItem(self, item):
        self.items.append(item)
        self.updateUI()
