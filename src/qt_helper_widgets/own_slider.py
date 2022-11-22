import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class OwnSlider(qtw.QSlider):
    def __init__(self):
        super(OwnSlider, self).__init__(qtc.Qt.Horizontal)

    def keyPressEvent(self, event) -> None:
        if event.key() == qtc.Qt.Key_Up:
            self.plus_step()
        elif event.key() == qtc.Qt.Key_Down:
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
