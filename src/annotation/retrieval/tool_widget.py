import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class RetrievalTools(qtw.QWidget):
    change_filter = qtc.pyqtSignal()
    accept_interval = qtc.pyqtSignal()
    reject_interval = qtc.pyqtSignal()
    modify_interval = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(RetrievalTools, self).__init__(*args, **kwargs)

        # Controll Attributes
        self.enabled = True

        self.init_UI()
        self.setEnabled(self.enabled)

    def init_UI(self):
        self.modify_filter_btn = qtw.QPushButton("Select Filter")
        self.modify_filter_btn.setStatusTip(
            "Change the filter by which the networks-predictions are queried."
        )
        self.modify_filter_btn.clicked.connect(lambda _: self.change_filter.emit())

        self.accept_button = qtw.QPushButton("Accept", self)
        self.accept_button.setStatusTip("Accept the suggested annotation.")
        self.accept_button.clicked.connect(lambda _: self.accept_interval.emit())

        self.modify_button = qtw.QPushButton("Modify", self)
        self.modify_button.setStatusTip("Modify the suggested annotation.")
        self.modify_button.clicked.connect(lambda _: self.modify_interval.emit())

        self.reject_button = qtw.QPushButton("Reject", self)
        self.reject_button.setStatusTip("Reject the suggested annotation.")
        self.reject_button.clicked.connect(lambda _: self.reject_interval.emit())

        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.accept_button)
        self.layout.addWidget(self.modify_button)
        self.layout.addWidget(self.reject_button)
        self.layout.addWidget(self.modify_filter_btn)

    @qtc.pyqtSlot(bool)
    def setEnabled(self, x: bool) -> None:
        self.enabled = x
        self.accept_button.setEnabled(x)
        self.modify_button.setEnabled(x)
        self.reject_button.setEnabled(x)
        self.modify_filter_btn.setEnabled(x)

    def isEnabled(self) -> bool:
        return self.enabled
