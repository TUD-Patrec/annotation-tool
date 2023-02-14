import PyQt6.QtCore as qtc
import PyQt6.QtWidgets as qtw


class OwnSlider(qtw.QSlider):
    def __init__(self):
        super(OwnSlider, self).__init__(qtc.Qt.Orientation.Horizontal)

    def keyPressEvent(self, event) -> None:
        if event.key() == qtc.Qt.Key.Key_Right:
            self.plus_step()
        elif event.key() == qtc.Qt.Key.Key_Left:
            self.minus_step()
        else:
            super(OwnSlider, self).keyPressEvent(event)

    def plus_step(self):
        """Increase slider to next multiple of single step."""
        rest = self.value() % self.singleStep()
        self.setValue(self.value() + self.singleStep() - rest)

    def minus_step(self):
        """Decrease slider to next multiple of single step."""
        rest = self.value() % self.singleStep()
        if rest:
            self.setValue(self.value() - rest)
        else:
            self.setValue(self.value() - self.singleStep())

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.plus_step()
        else:
            self.minus_step()
