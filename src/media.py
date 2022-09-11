import logging
import time

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from .media_backend.controller import QMediaMainController

class Media(qtw.QWidget):
       position_changed = qtc.pyqtSignal(int)       
       cleaned_up = qtc.pyqtSignal()
       
       def __init__(self, *args, **kwargs) -> None:
              super().__init__(*args, **kwargs)
              self.controller = QMediaMainController()
              self.controller.cleaned_up.connect(self.cleaned_up)
              self.controller.position_changed.connect(self.position_changed)
              self._layout = qtw.QHBoxLayout(self)
              self._layout.setContentsMargins(0,0,0,0)
              self._layout.addWidget(self.controller)
              
       @qtc.pyqtSlot(object)
       def load_annotation(self, o):
              self.controller.load_annotation(o)

       @qtc.pyqtSlot(int)
       def setPosition(self, p):
              self.controller.set_position(p)
       
       @qtc.pyqtSlot()
       def play(self):
              self.controller.play()
       
       @qtc.pyqtSlot()
       def pause(self):
              self.controller.pause()
       
       @qtc.pyqtSlot(float)
       def set_replay_speed(self, x):
              self.controller.set_replay_speed(x)
       
       @qtc.pyqtSlot()
       def settings_changed(self):
              self.controller.settings_changed()
       
       @qtc.pyqtSlot()
       def shutdown(self):
              self.controller.shutdown()