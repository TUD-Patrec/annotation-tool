from typing import Union

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.annotation.retrieval.retrieval_backend.element import RetrievalElement
from src.annotation.retrieval.retrieval_backend.query import Query
from src.qt_helper_widgets.display_scheme import QShowAnnotation
from src.qt_helper_widgets.histogram import HistogramWidget
from src.qt_helper_widgets.lines import QHLine


def format_progress(x, y):
    x += 1
    percentage = int(x * 100 / y) if y != 0 else 100
    return f"{x : }/{y}\t[{percentage}%] "


class QRetrievalWidget(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super(QRetrievalWidget, self).__init__(*args, **kwargs)
        self.init_UI()

    def init_UI(self):
        self.filter_widget = qtw.QWidget()
        self.filter_widget.setLayout(qtw.QHBoxLayout())
        self.filter_widget.layout().addWidget(qtw.QLabel("Filter:"))
        self.filter_active = qtw.QLabel("Inactive")
        self.filter_widget.layout().addWidget(self.filter_active)

        self.main_widget = QShowAnnotation(self)

        self.histogram = HistogramWidget()
        self.histogram.ensurePolished()  # updates style of the widget before presenting
        self.histogram.plot()

        # self.similarity_label = qtw.QLabel(self)
        self.progress_label = qtw.QLabel(format_progress(0, 0), self)

        self.footer_widget = qtw.QWidget()
        self.footer_widget.setLayout(qtw.QHBoxLayout())

        self.footer_widget.layout().addWidget(qtw.QLabel("Progress:", self))
        self.footer_widget.layout().addWidget(self.progress_label)

        vbox = qtw.QVBoxLayout()

        vbox.addWidget(self.filter_widget)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.main_widget, alignment=qtc.Qt.AlignCenter, stretch=1)
        vbox.addWidget(QHLine())

        vbox.addWidget(self.histogram, alignment=qtc.Qt.AlignCenter)
        vbox.addWidget(QHLine())
        vbox.addWidget(self.footer_widget, alignment=qtc.Qt.AlignCenter)

        vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vbox)
        self.setFixedWidth(400)

    @qtc.pyqtSlot(Query, object)
    def update_UI(
        self, query: Query, retrieval_element: Union[RetrievalElement, None]
    ) -> None:
        """
        Update the UI with the current element.

        Args:
            query: The query that was used to retrieve the element.
            retrieval_element: The element that was retrieved.
        """

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
            sim = None

        # Case 2: We're finished -> End of query reached
        elif retrieval_element is None:
            txt = format_progress(len(query) - 1, len(query))
            self.progress_label.setText(txt)
            sim = None

        # Case 3: Default - we're somewhere in the middle of the query
        else:
            txt = format_progress(query.current_index, len(query))
            self.progress_label.setText(txt)

            sim = retrieval_element._similarity

            proposed_annotation = retrieval_element.annotation
            self.main_widget.show_annotation(proposed_annotation)

        data = query.similarity_distribution

        if data.shape[0] > 0:
            self.histogram.plot(data, sim)
        else:
            self.histogram.reset()
