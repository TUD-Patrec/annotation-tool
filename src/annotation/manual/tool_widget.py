import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class ManualAnnotationTools(qtw.QWidget):
    annotate = qtc.pyqtSignal()
    cut = qtc.pyqtSignal()
    cut_and_annotate = qtc.pyqtSignal()
    merge = qtc.pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super(ManualAnnotationTools, self).__init__(*args, **kwargs)

        # Controll Attributes
        self.enabled = True

        self.init_UI()
        self.setEnabled(self.enabled)

    def init_UI(self):
        self.annotate_btn = qtw.QPushButton("Annotate", self)
        self.annotate_btn.setStatusTip(
            "Open the Annotation-Dialog for the highlighted sample."
        )
        self.annotate_btn.clicked.connect(self.annotate.emit)

        self.cut_btn = qtw.QPushButton("Cut", self)
        self.cut_btn.setStatusTip("Split the highlighted sample into two pieces.")
        self.cut_btn.clicked.connect(self.cut.emit)

        self.cut_and_annotate_btn = qtw.QPushButton("C+A", self)
        self.cut_and_annotate_btn.setStatusTip(
            "Cut and immediately annotate the current sample."
        )
        self.cut_and_annotate_btn.clicked.connect(self.cut_and_annotate.emit)

        self.merge_left_btn = qtw.QPushButton("Merge Left", self)
        self.merge_left_btn.setStatusTip(
            "Merge highlighted sample with the left neighbour."
        )
        self.merge_left_btn.clicked.connect(lambda _: self.merge.emit(True))

        self.merge_right_btn = qtw.QPushButton("Merge Right", self)
        self.merge_right_btn.setStatusTip(
            "Merge highlighted sample with the right neighbour"
        )
        self.merge_right_btn.clicked.connect(lambda _: self.merge.emit(False))

        # layout
        vbox = qtw.QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self.annotate_btn)
        vbox.addWidget(self.cut_btn)
        vbox.addWidget(self.cut_and_annotate_btn)
        vbox.addWidget(self.merge_left_btn)
        vbox.addWidget(self.merge_right_btn)

        self.setLayout(vbox)

    @qtc.pyqtSlot(bool)
    def setEnabled(self, x: bool) -> None:
        self.enabled = x
        self.annotate_btn.setEnabled(x)
        self.cut_btn.setEnabled(x)
        self.cut_and_annotate_btn.setEnabled(x)
        self.merge_left_btn.setEnabled(x)
        self.merge_right_btn.setEnabled(x)

    def isEnabled(self) -> bool:
        return self.enabled
