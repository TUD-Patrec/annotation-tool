import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.dataclasses.settings import Settings


def _read_from_txt(x: str, x_type, default):
    return x_type(x) if x != "" else default


class SettingsDialog(qtw.QDialog):
    settings_changed = qtc.pyqtSignal()
    window_size_changed = qtc.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)
        settings = Settings.instance()

        self.old_settings = settings.as_dict()

        form = qtw.QFormLayout()

        self.annotator_id = qtw.QLineEdit()
        form.addRow("Annotator_ID:", self.annotator_id)

        self.window_x = qtw.QLineEdit()
        form.addRow("Preferred Window_Width:", self.window_x)

        self.window_y = qtw.QLineEdit()
        form.addRow("Preferred Window_Height:", self.window_y)

        self.font_size = qtw.QComboBox()
        form.addRow("Font-Size:", self.font_size)

        self.darkmode = qtw.QCheckBox()
        form.addRow("Darkmode:", self.darkmode)

        self.refresh_rate = qtw.QLineEdit()
        form.addRow("MoCap FPS:", self.refresh_rate)

        self.frame_based = qtw.QComboBox()
        form.addRow("Timeline Style:", self.frame_based)

        self.small_skip = qtw.QSlider(qtc.Qt.Horizontal)
        self.small_skip_display = qtw.QLabel()
        small_skip_widget = qtw.QWidget()
        small_skip_widget.setLayout(qtw.QHBoxLayout())
        small_skip_widget.layout().addWidget(self.small_skip, stretch=1)
        small_skip_widget.layout().addWidget(self.small_skip_display)
        form.addRow("Distance small step:", small_skip_widget)

        self.big_skip = qtw.QSlider(qtc.Qt.Horizontal)
        self.big_skip_display = qtw.QLabel()
        big_skip_widget = qtw.QWidget()
        big_skip_widget.setLayout(qtw.QHBoxLayout())
        big_skip_widget.layout().addWidget(self.big_skip, stretch=1)
        big_skip_widget.layout().addWidget(self.big_skip_display)
        form.addRow("Distance big step:", big_skip_widget)

        self.debugging_mode = qtw.QCheckBox()
        form.addRow("Debugging-Mode:", self.debugging_mode)

        self.retrieval_segment_size = qtw.QLineEdit()
        form.addRow("Segment size in retrieval-mode:", self.retrieval_segment_size)

        self.retrieval_segment_overlap = qtw.QLineEdit()
        form.addRow(
            "Segment overlap in retrieval-mode:", self.retrieval_segment_overlap
        )

        self.save_button = qtw.QPushButton()
        self.save_button.setText("Save")
        self.save_button.clicked.connect(lambda _: self.save_pressed())

        self.reset_button = qtw.QPushButton()
        self.reset_button.setText("Reset to Default")
        self.reset_button.clicked.connect(lambda _: self.reset_pressed())

        self.cancel_button = qtw.QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(lambda _: self.cancel_pressed())

        self.button_widget = qtw.QWidget()
        self.button_widget.setLayout(qtw.QHBoxLayout())
        self.button_widget.layout().addWidget(self.save_button)
        self.button_widget.layout().addWidget(self.reset_button)
        self.button_widget.layout().addWidget(self.cancel_button)

        form.addRow(self.button_widget)
        form.setAlignment(qtc.Qt.AlignCenter)

        self.setLayout(form)
        self.load_layout()
        self.adjustSize()
        self.setFixedSize(self.size())

    def load_layout(self):
        settings = Settings.instance()
        x_min, y_min, x_max, y_max = 720, 576, 5000, 5000

        id_validator = qtg.QIntValidator(self)
        self.annotator_id.setText(str(settings.annotator_id))
        self.annotator_id.setValidator(id_validator)
        self.annotator_id.setPlaceholderText(str(0))

        x_validator = qtg.QIntValidator(x_min, x_max, self)
        self.window_x.setValidator(x_validator)
        self.window_x.setText(str(settings.window_x))
        self.window_x.setPlaceholderText(str(settings.window_x))

        y_validator = qtg.QIntValidator(y_min, y_max, self)
        self.window_y.setValidator(y_validator)
        self.window_y.setText(str(settings.window_y))
        self.window_y.setPlaceholderText(str(settings.window_y))

        for x in range(6, 17):
            self.font_size.addItem(str(x))

        self.font_size.setCurrentIndex(settings.font - 6)

        self.darkmode.setChecked(settings.darkmode)

        refresh_validator = qtg.QIntValidator(1, 500, self)
        self.refresh_rate.setValidator(refresh_validator)
        self.refresh_rate.setText(str(settings.refresh_rate))
        self.refresh_rate.setPlaceholderText(str(200))

        show_millis = settings.show_millisecs
        self.frame_based.addItem("Show frame numbers")
        self.frame_based.addItem("Show timestamps")
        self.frame_based.setCurrentIndex(int(show_millis))

        self.small_skip.setRange(1, 10)
        self.small_skip.setTickInterval(1)
        self.small_skip.setSingleStep(1)
        self.small_skip.setTickPosition(qtw.QSlider.TicksBelow)
        self.small_skip.setValue(settings.small_skip)
        self.small_skip.valueChanged.connect(
            lambda x: self.small_skip_display.setText("{} [frames]".format(x))
        )
        self.small_skip_display.setText("{} [frames]".format(settings.small_skip))
        self.small_skip_display.setAlignment(qtc.Qt.AlignRight)
        self.small_skip_display.setFixedWidth(75)

        self.debugging_mode.setChecked(settings.debugging_mode)

        self.big_skip.setRange(50, 500)
        self.big_skip.setTickInterval(50)
        self.big_skip.setSingleStep(50)
        self.big_skip.setTickPosition(qtw.QSlider.TicksBelow)
        self.big_skip.setValue(settings.big_skip)
        self.big_skip.valueChanged.connect(
            lambda x: self.big_skip_display.setText("{} [frames]".format(x))
        )
        self.big_skip_display.setText("{} [frames]".format(settings.big_skip))
        self.big_skip_display.setAlignment(qtc.Qt.AlignRight)
        self.big_skip_display.setFixedWidth(75)

        segment_validator = qtg.QIntValidator(100, 10000, self)
        self.retrieval_segment_size.setValidator(segment_validator)
        self.retrieval_segment_size.setText(str(settings.retrieval_segment_size))
        self.retrieval_segment_size.setPlaceholderText(str(200))

        overlap_validator = qtg.QDoubleValidator(0, 0.99, 2, self)
        self.retrieval_segment_overlap.setValidator(overlap_validator)
        self.retrieval_segment_overlap.setText(str(settings.retrieval_segment_overlap))
        self.retrieval_segment_overlap.setPlaceholderText(str(0))

    def save_pressed(self):
        settings = Settings.instance()

        old_x, old_y = settings.window_x, settings.window_y

        settings.annotator_id = _read_from_txt(
            self.annotator_id.text(), int, self.annotator_id.placeholderText()
        )
        settings.debugging_mode = self.debugging_mode.isChecked()
        settings.window_x = _read_from_txt(
            self.window_x.text(), int, self.window_x.placeholderText()
        )
        settings.window_y = _read_from_txt(
            self.window_y.text(), int, self.window_y.placeholderText()
        )
        settings.font = int(self.font_size.currentText())
        settings.darkmode = self.darkmode.isChecked()
        settings.refresh_rate = _read_from_txt(
            self.refresh_rate.text(), int, self.refresh_rate.placeholderText()
        )
        settings.show_millisecs = bool(self.frame_based.currentIndex())
        settings.small_skip = self.small_skip.value()
        settings.big_skip = self.big_skip.value()
        settings.retrieval_segment_size = _read_from_txt(
            self.retrieval_segment_size.text(),
            int,
            self.retrieval_segment_size.placeholderText(),
        )
        settings.retrieval_segment_overlap = _read_from_txt(
            self.retrieval_segment_overlap.text(),
            float,
            self.retrieval_segment_overlap.placeholderText(),
        )

        settings.to_disk()

        if old_x != settings.window_x or old_y != settings.window_y:
            self.window_size_changed.emit(settings.window_x, settings.window_y)

        self.settings_changed.emit()
        self.close()

    def reset_pressed(self):
        settings = Settings.instance()
        settings.reset()
        self.load_layout()

    def cancel_pressed(self):
        Settings.instance().from_dict(self.old_settings)
        self.close()


if __name__ == "__main__":
    import sys

    app = qtw.QApplication(sys.argv)
    # MainWindow = GUI()
    MainWindow = SettingsDialog("C:")
    MainWindow.show()
    sys.exit(app.exec_())
