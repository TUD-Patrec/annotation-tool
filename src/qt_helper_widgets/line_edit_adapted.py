import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class QLineEditAdapted(qtw.QLineEdit):
    mousePressed = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QLineEditAdapted, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.mousePressed.emit()

    def keyPressEvent(self, event):
        if event.key() in [qtc.Qt.Key_Enter, qtc.Qt.Key_Space]:
            self.mousePressed.emit()
