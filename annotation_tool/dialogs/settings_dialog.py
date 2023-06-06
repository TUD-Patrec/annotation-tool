import logging

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.settings import settings


class SettingsDialog(qtw.QDialog):
    window_size_changed = qtc.pyqtSignal(int, int)
    settings_changed = qtc.pyqtSignal()

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)

        self.layout = qtw.QVBoxLayout()

        # annotator ID
        self.annotator_id_layout = qtw.QHBoxLayout()
        self.annotator_id_label = qtw.QLabel("Annotator ID:")
        self.annotator_id_edit = qtw.QLineEdit()
        only_int = qtg.QIntValidator()
        self.annotator_id_edit.setText(str(self.settings.annotator_id))
        self.annotator_id_edit.setValidator(only_int)
        self.annotator_id_edit.setMaxLength(3)
        self.annotator_id_edit.textChanged.connect(self.annotator_id_changed)
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
        self.developer_settings_layout = qtw.QHBoxLayout()
        self.developer_settings_label = qtw.QLabel("Developer Settings:")
        self.developer_settings_button = qtw.QPushButton("Change")
        self.developer_settings_button.clicked.connect(self.change_developer_settings)
        self.developer_settings_layout.addWidget(self.developer_settings_label)
        self.developer_settings_layout.addWidget(self.developer_settings_button)
        self.layout.addLayout(self.developer_settings_layout)

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

        self.reset_button.setDisabled(True)
        self.reset_button.hide()

    def change_appearance(self):
        dlg = AppearanceSettingsDialog(self)
        dlg.window_size_changed.connect(self.window_size_changed.emit)
        dlg.exec()
        dlg.deleteLater()

    def change_developer_settings(self):
        dlg = DeveloperSettingsDialog(self)
        dlg.settings_changed.connect(self.settings_changed.emit)
        dlg.exec()
        dlg.deleteLater()

    def change_navigation(self):
        dlg = NavigationSettingsDialog(self)
        dlg.exec()
        dlg.deleteLater()

    def change_retrieval_mode(self):
        dlg = RetrievalSettingsDialog(self)
        dlg.exec()
        dlg.deleteLater()

    def reset_settings(self):
        self.annotator_id_edit.setText(str(self.settings.get_default("annotator_id")))

    def annotator_id_changed(self):
        if self.annotator_id_edit.text() != "":
            self.settings.annotator_id = int(self.annotator_id_edit.text())

    def accept(self):
        # only allow numbers in annotator ID field
        if self.annotator_id_edit.text().isnumeric():
            self.settings.annotator_id = int(self.annotator_id_edit.text())
        else:
            self.annotator_id_edit.setText(str(self.settings.annotator_id))
        super().accept()


class AppearanceSettingsDialog(qtw.QDialog):
    window_size_changed = qtc.pyqtSignal(int, int)
    font_size_changed = qtc.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Appearance Settings")
        self.setFixedSize(400, 300)

        self.layout = qtw.QVBoxLayout()

        # theme
        self.theme_layout = qtw.QHBoxLayout()
        self.theme_label = qtw.QLabel("Theme:")
        self.theme_combobox = qtw.QComboBox()
        self.theme_combobox.addItems(["Light", "Dark"])  # for now disable System theme
        idx = self.theme_combobox.findText(settings.color_theme.capitalize())
        self.theme_combobox.setCurrentIndex(idx)
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
        self.preferred_width_spinbox.setRange(1200, 4000)
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
        self.preferred_height_spinbox.setRange(700, 2000)
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

        # timeline design
        self.timeline_design_layout = qtw.QHBoxLayout()
        self.timeline_design_label = qtw.QLabel("Timeline Design:")
        self.timeline_design_combobox = qtw.QComboBox()
        self.timeline_design_combobox.addItems(["Rounded", "Rectangular"])
        idx = self.timeline_design_combobox.findText(
            settings.timeline_design.capitalize()
        )
        self.timeline_design_combobox.setCurrentIndex(idx)
        self.timeline_design_combobox.currentTextChanged.connect(
            self.change_timeline_design
        )
        self.timeline_design_layout.addWidget(self.timeline_design_label)
        self.timeline_design_layout.addWidget(self.timeline_design_combobox)
        self.layout.addLayout(self.timeline_design_layout)

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
        default_color_scheme = settings.get_default("color_theme")
        _idx = self.theme_combobox.findText(default_color_scheme.capitalize())
        self.theme_combobox.setCurrentIndex(_idx)
        self.font_size_spinbox.setValue(settings.get_default("font_size"))
        self.preferred_width_spinbox.setValue(settings.get_default("preferred_width"))
        self.preferred_height_spinbox.setValue(settings.get_default("preferred_height"))
        self.timeline_design_combobox.setCurrentIndex(
            self.timeline_design_combobox.findText(
                settings.get_default("timeline_design").capitalize()
            )
        )

    def change_theme(self):
        mode = self.theme_combobox.currentText().lower()
        settings.color_theme = mode
        qtw.QApplication.instance().update_theme()

    def preferred_width_changed(self, value):
        # grab the main window
        settings.preferred_width = value
        self.window_size_changed.emit(value, settings.preferred_height)

    def preferred_height_changed(self, value):
        settings.preferred_height = value
        self.window_size_changed.emit(settings.preferred_width, value)

    def change_font_size(self, value):
        settings.font_size = value
        qtw.QApplication.instance().update_theme()

    def change_timeline_design(self, value):
        settings.timeline_design = value.lower()
        qtw.QApplication.instance().timeline.update()


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

        # Merging mode
        self.merge_mode_layout = qtw.QHBoxLayout()
        self.merge_mode_label = qtw.QLabel("Merging behavior:")
        self.merge_mode_combobox = qtw.QComboBox()
        self.merge_mode_combobox.addItems(
            ["Use own annotation", "Use annotation from neighbor"]
        )
        idx = 1 if settings.merging_mode == "into" else 0
        self.merge_mode_combobox.setCurrentIndex(idx)
        self.merge_mode_combobox.currentIndexChanged.connect(self.change_merge_mode)
        self.merge_mode_layout.addWidget(self.merge_mode_label)
        self.merge_mode_layout.addWidget(self.merge_mode_combobox)
        self.layout.addLayout(self.merge_mode_layout)

        # Small skip
        self.small_skip_layout = qtw.QHBoxLayout()
        self.small_skip_label = qtw.QLabel("Skip:")
        self.small_skip_spinbox = qtw.QSpinBox()
        self.small_skip_spinbox.setRange(1, 100)
        self.small_skip_spinbox.setValue(settings.small_skip)
        self.small_skip_spinbox.valueChanged.connect(self.change_small_skip)
        self.small_skip_layout.addWidget(self.small_skip_label)
        self.small_skip_layout.addWidget(self.small_skip_spinbox)
        self.layout.addLayout(self.small_skip_layout)

        # Big skip
        self.big_skip_layout = qtw.QHBoxLayout()
        self.big_skip_label = qtw.QLabel("Quick skip:")
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

    def change_merge_mode(self, idx: int) -> None:
        settings.merging_mode = "into" if idx == 1 else "from"

    def reset_settings(self):
        self.small_skip_spinbox.setValue(settings.get_default("small_skip"))
        self.big_skip_spinbox.setValue(settings.get_default("big_skip"))
        self.merge_mode_combobox.setCurrentIndex(
            1 if settings.get_default("merging_mode") == "into" else 0
        )


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


class DeveloperSettingsDialog(qtw.QDialog):
    settings_changed = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._idx_to_log_lvl = {
            0: logging.DEBUG,
            1: logging.INFO,
            2: logging.WARNING,
            3: logging.ERROR,
            4: logging.CRITICAL,
        }
        self._log_lvl_to_idx = {v: k for k, v in self._idx_to_log_lvl.items()}

        self.init_ui()

    def init_ui(self):
        # set window title
        self.setWindowTitle("Developer Settings")
        self.setFixedSize(400, 300)

        # layout
        self.layout = qtw.QVBoxLayout()

        # Debug mode
        self.logging_layout = qtw.QHBoxLayout()
        self.logging_label = qtw.QLabel("Logging level:")
        self.logging_level_combobox = qtw.QComboBox()
        self.logging_level_combobox.addItems(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        current_idx = self._log_lvl_to_idx.get(settings.logging_level, 2)
        self.logging_level_combobox.setCurrentIndex(current_idx)
        self.logging_level_combobox.currentIndexChanged.connect(
            self.change_logging_level
        )
        self.logging_layout.addWidget(self.logging_label)
        self.logging_layout.addWidget(self.logging_level_combobox)
        self.layout.addLayout(self.logging_layout)

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

    def change_logging_level(self, idx: int) -> None:
        settings.logging_level = self._idx_to_log_lvl[idx]
        self.settings_changed.emit()

    def reset_settings(self):
        default_logging_level = settings.get_default("logging_level")
        self.logging_level_combobox.setCurrentIndex(
            self._log_lvl_to_idx[default_logging_level]
        )
        self.settings_changed.emit()
