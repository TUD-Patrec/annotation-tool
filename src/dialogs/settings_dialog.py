import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.settings import settings


class SettingsDialog(qtw.QDialog):
    window_size_changed = qtc.pyqtSignal(int, int)
    settings_changed = qtc.pyqtSignal()

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setWindowFlags(
            qtc.Qt.WindowCloseButtonHint | qtc.Qt.WindowMinimizeButtonHint
        )
        self.setFixedSize(400, 300)

        self.layout = qtw.QVBoxLayout()

        # annotator ID
        self.annotator_id_layout = qtw.QHBoxLayout()
        self.annotator_id_label = qtw.QLabel("Annotator ID:")
        self.annotator_id_edit = qtw.QLineEdit()
        self.annotator_id_edit.setText(str(self.settings.annotator_id))
        self.annotator_id_layout.addWidget(self.annotator_id_label)
        self.annotator_id_layout.addWidget(self.annotator_id_edit)
        self.layout.addLayout(self.annotator_id_layout)

        # appearance sub-menu
        self.appearance_layout = qtw.QHBoxLayout()
        self.appearance_label = qtw.QLabel("Appearance:")
        self.appearance_button = qtw.QPushButton("Change")
        self.appearance_button.clicked.connect(self.change_appearance)
        self.appearance_layout.addWidget(self.appearance_label)
        self.appearance_layout.addWidget(self.appearance_button)
        self.layout.addLayout(self.appearance_layout)

        # media sub-menu
        self.media_layout = qtw.QHBoxLayout()
        self.media_label = qtw.QLabel("Media:")
        self.media_button = qtw.QPushButton("Change")
        self.media_button.clicked.connect(self.change_media)
        self.media_layout.addWidget(self.media_label)
        self.media_layout.addWidget(self.media_button)
        self.layout.addLayout(self.media_layout)

        # navigation sub-menu
        self.navigation_layout = qtw.QHBoxLayout()
        self.navigation_label = qtw.QLabel("Navigation:")
        self.navigation_button = qtw.QPushButton("Change")
        self.navigation_button.clicked.connect(self.change_navigation)
        self.navigation_layout.addWidget(self.navigation_label)
        self.navigation_layout.addWidget(self.navigation_button)
        self.layout.addLayout(self.navigation_layout)

        # retrieval-mode sub-menu
        self.retrieval_mode_layout = qtw.QHBoxLayout()
        self.retrieval_mode_label = qtw.QLabel("Retrieval Mode:")
        self.retrieval_moode_button = qtw.QPushButton("Change")
        self.retrieval_moode_button.clicked.connect(self.change_retrieval_mode)
        self.retrieval_mode_layout.addWidget(self.retrieval_mode_label)
        self.retrieval_mode_layout.addWidget(self.retrieval_moode_button)
        self.layout.addLayout(self.retrieval_mode_layout)

        # enable developer mode
        self.developer_mode_layout = qtw.QHBoxLayout()
        self.developer_mode_label = qtw.QLabel("Developer Mode:")
        self.developer_mode_checkbox = qtw.QCheckBox()
        self.developer_mode_checkbox.setChecked(self.settings.debugging_mode)
        self.developer_mode_layout.addWidget(self.developer_mode_label)
        self.developer_mode_layout.addWidget(self.developer_mode_checkbox)
        self.layout.addLayout(self.developer_mode_layout)

        # Accept, Reset and Cancel buttons
        self.button_layout = qtw.QHBoxLayout()
        self.reset_button = qtw.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addStretch()
        self.accept_button = qtw.QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.accept_button)
        self.cancel_button = qtw.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def change_appearance(self):
        dlg = AppearanceSettingsDialog(self)
        dlg.window_size_changed.connect(self.window_size_changed.emit)
        dlg.exec_()
        dlg.deleteLater()

    def change_media(self):
        dlg = MediaSettingsDialog(self)
        dlg.settings_changed.connect(self.settings_changed.emit)
        dlg.exec_()
        dlg.deleteLater()

    def change_navigation(self):
        dlg = NavigationSettingsDialog(self)
        dlg.exec_()
        dlg.deleteLater()

    def change_retrieval_mode(self):
        dlg = RetrievalSettingsDialog(self)
        dlg.exec_()
        dlg.deleteLater()

    def reset_settings(self):
        self.annotator_id_edit.setText(str(self.settings.get_default("annotator_id")))
        self.developer_mode_checkbox.setChecked(
            self.settings.get_default("debugging_mode")
        )

    def accept(self):
        # only allow numbers in annotator ID field
        if self.annotator_id_edit.text().isnumeric():
            self.settings.annotator_id = int(self.annotator_id_edit.text())
        else:
            self.annotator_id_edit.setText(str(self.settings.annotator_id))
        self.settings.debugging_mode = self.developer_mode_checkbox.isChecked()
        self.settings_changed.emit()
        super().accept()


class AppearanceSettingsDialog(qtw.QDialog):
    window_size_changed = qtc.pyqtSignal(int, int)
    font_size_changed = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

        from src.main_controller import get_app

        self.app = get_app()

    def init_ui(self):
        self.setWindowTitle("Appearance Settings")
        self.setFixedSize(400, 300)

        self.layout = qtw.QVBoxLayout()

        # theme
        self.theme_layout = qtw.QHBoxLayout()
        self.theme_label = qtw.QLabel("Theme:")
        self.theme_combobox = qtw.QComboBox()
        self.theme_combobox.addItems(["Light", "Dark"])
        self.theme_combobox.setCurrentIndex(1 if settings.darkmode else 0)
        self.theme_combobox.currentIndexChanged.connect(self.change_theme)
        self.theme_layout.addWidget(self.theme_label)
        self.theme_layout.addWidget(self.theme_combobox)
        self.layout.addLayout(self.theme_layout)

        # font size
        self.font_size_layout = qtw.QHBoxLayout()
        self.font_size_label = qtw.QLabel("Font Size:")
        self.font_size_spinbox = qtw.QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setValue(settings.font_size)
        self.font_size_spinbox.valueChanged.connect(self.change_font_size)
        self.font_size_layout.addWidget(self.font_size_label)
        self.font_size_layout.addWidget(self.font_size_spinbox)
        self.layout.addLayout(self.font_size_layout)

        # preferred width
        self.preferred_width_layout = qtw.QHBoxLayout()
        self.preferred_width_label = qtw.QLabel("Preferred Width:")
        self.preferred_width_spinbox = qtw.QSpinBox()
        self.preferred_width_spinbox.setRange(600, 4000)
        self.preferred_width_spinbox.setSingleStep(100)
        self.preferred_width_spinbox.setValue(settings.preferred_width)
        self.preferred_width_spinbox.valueChanged.connect(self.preferred_width_changed)
        self.preferred_width_layout.addWidget(self.preferred_width_label)
        self.preferred_width_layout.addWidget(self.preferred_width_spinbox)
        self.layout.addLayout(self.preferred_width_layout)

        # preferred height
        self.preferred_height_layout = qtw.QHBoxLayout()
        self.preferred_height_label = qtw.QLabel("Preferred Height:")
        self.preferred_height_spinbox = qtw.QSpinBox()
        self.preferred_height_spinbox.setRange(400, 2000)
        self.preferred_height_spinbox.setSingleStep(100)
        self.preferred_height_spinbox.setValue(settings.preferred_height)
        self.preferred_height_spinbox.valueChanged.connect(
            self.preferred_height_changed
        )
        self.preferred_height_layout.addWidget(self.preferred_height_label)
        self.preferred_height_layout.addWidget(self.preferred_height_spinbox)
        self.layout.addLayout(self.preferred_height_layout)

        # high DPI scaling
        self.high_dpi_scaling_layout = qtw.QHBoxLayout()
        self.high_dpi_scaling_label = qtw.QLabel("High DPI Scaling:")
        self.high_dpi_scaling_label.setToolTip(
            "Changing this will only take effect after a restart."
        )
        self.high_dpi_scaling_checkbox = qtw.QCheckBox()
        self.high_dpi_scaling_checkbox.setToolTip(
            "Changing this will only take effect after a restart."
        )
        self.high_dpi_scaling_checkbox.setChecked(settings.high_dpi_scaling)
        self.high_dpi_scaling_checkbox.stateChanged.connect(
            self.change_high_dpi_scaling
        )
        self.high_dpi_scaling_layout.addWidget(self.high_dpi_scaling_label)
        self.high_dpi_scaling_layout.addWidget(self.high_dpi_scaling_checkbox)
        self.layout.addLayout(self.high_dpi_scaling_layout)

        # Accept, Reset buttons
        self.button_layout = qtw.QHBoxLayout()
        self.accept_button = qtw.QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        self.reset_button = qtw.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        self.button_layout.addWidget(self.accept_button)
        self.button_layout.addWidget(self.reset_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def reset_settings(self):
        self.theme_combobox.setCurrentIndex(
            1 if settings.get_default("darkmode") else 0
        )
        self.font_size_spinbox.setValue(settings.get_default("font_size"))
        self.preferred_width_spinbox.setValue(settings.get_default("preferred_width"))
        self.preferred_height_spinbox.setValue(settings.get_default("preferred_height"))
        self.high_dpi_scaling_checkbox.setChecked(
            settings.get_default("high_dpi_scaling")
        )

    def change_theme(self):
        is_darkmode = bool(self.theme_combobox.currentIndex())
        settings.darkmode = is_darkmode
        self.app.update_theme()

    def preferred_width_changed(self, value):
        # grab the main window
        settings.preferred_width = value
        self.window_size_changed.emit(value, settings.preferred_height)

    def preferred_height_changed(self, value):
        settings.preferred_height = value
        self.window_size_changed.emit(settings.preferred_width, value)

    def change_font_size(self, value):
        settings.font_size = value
        self.app.update_font()

    def change_high_dpi_scaling(self, value):
        settings.high_dpi_scaling = bool(value)


class MediaSettingsDialog(qtw.QDialog):
    settings_changed = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # set window title
        self.setWindowTitle("Media Settings")
        self.setFixedSize(400, 300)

        # layout
        self.layout = qtw.QVBoxLayout()

        # fallback FPS if no FPS is detected
        self.fallback_fps_layout = qtw.QHBoxLayout()
        self.fallback_fps_label = qtw.QLabel("Fallback FPS:")
        # slider for fallback FPS
        self.fallback_fps_slider = qtw.QSlider(qtc.Qt.Horizontal)
        self.fallback_fps_slider.setRange(1, 250)
        # display the current value of the slider
        self.fallback_display = qtw.QLabel(str(settings.refresh_rate))
        self.fallback_fps_slider.valueChanged.connect(self.change_fallback_fps)
        self.fallback_fps_layout.addWidget(self.fallback_fps_label)
        self.fallback_fps_slider.setValue(settings.refresh_rate)
        self.fallback_fps_layout.addWidget(self.fallback_fps_slider)
        self.fallback_fps_layout.addWidget(self.fallback_display)
        self.layout.addLayout(self.fallback_fps_layout)

        # Accept, Reset buttons
        self.button_layout = qtw.QHBoxLayout()
        self.accept_button = qtw.QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        self.reset_button = qtw.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        self.button_layout.addWidget(self.accept_button)
        self.button_layout.addWidget(self.reset_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def change_fallback_fps(self, value: int) -> None:
        settings.refresh_rate = value
        self.fallback_display.setText(str(value))
        self.settings_changed.emit()

    def reset_settings(self):
        self.fallback_fps_slider.setValue(settings.get_default("refresh_rate"))


class NavigationSettingsDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # set window title
        self.setWindowTitle("Navigation Settings")
        self.setFixedSize(400, 300)

        # layout
        self.layout = qtw.QVBoxLayout()

        # Small skip
        self.small_skip_layout = qtw.QHBoxLayout()
        self.small_skip_label = qtw.QLabel("Small skip:")
        self.small_skip_spinbox = qtw.QSpinBox()
        self.small_skip_spinbox.setRange(1, 100)
        self.small_skip_spinbox.setValue(settings.small_skip)
        self.small_skip_spinbox.valueChanged.connect(self.change_small_skip)
        self.small_skip_layout.addWidget(self.small_skip_label)
        self.small_skip_layout.addWidget(self.small_skip_spinbox)
        self.layout.addLayout(self.small_skip_layout)

        # Big skip
        self.big_skip_layout = qtw.QHBoxLayout()
        self.big_skip_label = qtw.QLabel("Big skip:")
        self.big_skip_spinbox = qtw.QSpinBox()
        self.big_skip_spinbox.setRange(100, 5000)
        self.big_skip_spinbox.setSingleStep(100)
        self.big_skip_spinbox.setValue(settings.big_skip)
        self.big_skip_spinbox.valueChanged.connect(self.change_big_skip)
        self.big_skip_layout.addWidget(self.big_skip_label)
        self.big_skip_layout.addWidget(self.big_skip_spinbox)
        self.layout.addLayout(self.big_skip_layout)

        # Accept, Reset buttons
        self.button_layout = qtw.QHBoxLayout()
        self.accept_button = qtw.QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        self.reset_button = qtw.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        self.button_layout.addWidget(self.accept_button)
        self.button_layout.addWidget(self.reset_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def change_small_skip(self, value: int) -> None:
        settings.small_skip = value

    def change_big_skip(self, value: int) -> None:
        settings.big_skip = value

    def reset_settings(self):
        self.small_skip_spinbox.setValue(settings.get_default("small_skip"))
        self.big_skip_spinbox.setValue(settings.get_default("big_skip"))


class RetrievalSettingsDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # set window title
        self.setWindowTitle("Retrieval Settings")
        self.setFixedSize(400, 300)

        # layout
        self.layout = qtw.QVBoxLayout()

        # Segment size
        self.segment_size_layout = qtw.QHBoxLayout()
        self.segment_size_label = qtw.QLabel("Segment size:")
        self.segment_size_spinbox = qtw.QSpinBox()
        self.segment_size_spinbox.setRange(100, 10000)
        self.segment_size_spinbox.setSingleStep(100)
        self.segment_size_spinbox.setValue(settings.retrieval_segment_size)
        self.segment_size_spinbox.valueChanged.connect(self.change_segment_size)
        self.segment_size_layout.addWidget(self.segment_size_label)
        self.segment_size_layout.addWidget(self.segment_size_spinbox)
        self.layout.addLayout(self.segment_size_layout)

        # Segment overlap double spinbox
        self.segment_overlap_layout = qtw.QHBoxLayout()
        self.segment_overlap_label = qtw.QLabel("Segment overlap:")
        self.segment_overlap_spinbox = qtw.QDoubleSpinBox()
        self.segment_overlap_spinbox.setRange(0, 0.95)
        self.segment_overlap_spinbox.setSingleStep(0.05)
        self.segment_overlap_spinbox.setValue(settings.retrieval_segment_overlap)
        self.segment_overlap_spinbox.valueChanged.connect(self.change_segment_overlap)
        self.segment_overlap_layout.addWidget(self.segment_overlap_label)
        self.segment_overlap_layout.addWidget(self.segment_overlap_spinbox)
        self.layout.addLayout(self.segment_overlap_layout)

        # Accept, Reset buttons
        self.button_layout = qtw.QHBoxLayout()
        self.accept_button = qtw.QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        self.reset_button = qtw.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        self.button_layout.addWidget(self.accept_button)
        self.button_layout.addWidget(self.reset_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def change_segment_size(self, value: int) -> None:
        settings.retrieval_segment_size = value

    def change_segment_overlap(self, value: float) -> None:
        settings.retrieval_segment_overlap = value

    def reset_settings(self):
        self.segment_size_spinbox.setValue(
            settings.get_default("retrieval_segment_size")
        )
        self.segment_overlap_spinbox.setValue(
            settings.get_default("retrieval_segment_overlap")
        )
