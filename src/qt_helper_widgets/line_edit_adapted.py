import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

class QLineEditAdapted(qtw.QLineEdit):
    mousePressed = qtc.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(QLineEditAdapted, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.mousePressed.emit()