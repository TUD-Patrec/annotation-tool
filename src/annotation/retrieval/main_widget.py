import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.annotation.retrieval.retrieval_backend.query import Query
from src.qt_helper_widgets.display_scheme import QShowAnnotation
from src.qt_helper_widgets.histogram import Histogram_Widget
from src.qt_helper_widgets.lines import QHLine
from src.utility.decorators import accepts


def format_progress(x, y):
    x += 1
    percentage = int(x * 100 / y) if y != 0 else 100
    return f"{x : }/{y}\t[{percentage}%] "


class QRetrievalWidget(qtw.QWidget):
    change_filter = qtc.pyqtSignal()
    accept_interval = qtc.pyqtSignal()
    reject_interval = qtc.pyqtSignal()
    modify_interval = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QRetrievalWidget, self).__init__(*args, **kwargs)
        self.is_enabled = True
        self.init_UI()

    def init_UI(self):
        self.filter_widget = qtw.QWidget()
        self.filter_widget.setLayout(qtw.QHBoxLayout())
        self.filter_widget.layout().addWidget(qtw.QLabel("Filter:"))
        self.filter_active = qtw.QLabel("Inactive")
        self.modify_filter = qtw.QPushButton("Select Filter")
        self.modify_filter.clicked.connect(lambda _: self.change_filter.emit())
        self.filter_widget.layout().addWidget(self.filter_active)
        self.filter_widget.layout().addWidget(self.modify_filter)

        self.main_widget = QShowAnnotation(self)

        self.histogram = Histogram_Widget()

        self.button_group = qtw.QWidget()
        self.button_group.setLayout(qtw.QHBoxLayout())

        self.accept_button = qtw.QPushButton("ACCEPT", self)
        self.accept_button.clicked.connect(lambda _: self.accept_interval.emit())
        self.button_group.layout().addWidget(self.accept_button)

        self.modify_button = qtw.QPushButton("MODIFY", self)
        self.modify_button.clicked.connect(lambda _: self.modify_interval.emit())
        self.button_group.layout().addWidget(self.modify_button)

        self.reject_button = qtw.QPushButton("REJECT", self)
        self.reject_button.clicked.connect(lambda _: self.reject_interval.emit())
        self.button_group.layout().addWidget(self.reject_button)

        self.similarity_label = qtw.QLabel(self)
        self.progress_label = qtw.QLabel(format_progress(0, 0), self)

        self.footer_widget = qtw.QWidget()
        self.footer_widget.setLayout(qtw.QGridLayout())
        self.footer_widget.layout().addWidget(qtw.QLabel("Similarity", self), 0, 0)
        self.footer_widget.layout().addWidget(self.similarity_label, 0, 1)

        self.footer_widget.layout().addWidget(qtw.QLabel("Progress:", self), 1, 0)
        self.footer_widget.layout().addWidget(self.progress_label, 1, 1)

        vbox = qtw.QVBoxLayout()

        vbox.addWidget(self.filter_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.main_widget, alignment=qtc.Qt.AlignCenter, stretch=1)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.histogram)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.button_group, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.footer_widget, alignment=qtc.Qt.AlignCenter)
        self.setLayout(vbox)
        self.setFixedWidth(400)

    # Display the current interval to the user:
    # Show him the Interval boundaries and the predicted annotation
    @qtc.pyqtSlot(Query, object)
    def update_UI(self, query, current_interval):
        if query is None:
            self.progress_label.setText("_/_")
            self.histogram.reset()
            return

        filter_active_txt = (
            "Inactive" if query.filter_criterion.is_empty() else "Active"
        )
        self.filter_active.setText(filter_active_txt)

        # Case 1: Query is empty
        if len(query) == 0:
            self.progress_label.setText("Empty query")
            self.main_widget.show_annotation(None)
            sim = 0

        # Case 2: We're finished -> End of query reached
        elif current_interval is None:
            txt = format_progress(len(query) - 1, len(query))
            self.progress_label.setText(txt)
            sim = 0

        # Case 3: Default - we're somewhere in the middle of the query
        else:
            txt = format_progress(query.idx, len(query))
            self.progress_label.setText(txt)

            proposed_annotation = current_interval.annotation
            self.main_widget.show_annotation(proposed_annotation)

            sim = current_interval.similarity

        data = query.similarity_distribution()
        self.similarity_label.setText(f"{sim :.3f}")

        if data.shape[0] > 0:
            self.histogram.plot_data(data, sim)
        else:
            self.histogram.reset()

    @accepts(object, bool)
    def setEnabled(self, enabled: bool) -> None:
        self.is_enabled = enabled
        self.accept_button.setEnabled(enabled)
        self.modify_button.setEnabled(enabled)
        self.modify_filter.setEnabled(enabled)
        self.reject_button.setEnabled(enabled)
