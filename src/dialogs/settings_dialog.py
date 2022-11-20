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
        if dlg.exec_():
            self.settings_changed.emit()
        dlg.deleteLater()

    def change_media(self):
        dlg = qtw.QDialog(self)
        dlg.setWindowTitle("Media Settings")
        dlg.setFixedSize(400, 300)
        self.dlg = dlg
        dlg.exec_()

    def change_navigation(self):
        pass

    def change_retrieval_mode(self):
        pass

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

    def reject(self):
        super().reject()


class AppearanceSettingsDialog(qtw.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Appearance Settings")
        self.setFixedSize(400, 300)

        self.layout = qtw.QVBoxLayout()

        # theme
        self.theme_layout = qtw.QHBoxLayout()
        self.theme_label = qtw.QLabel("Theme:")
        self.theme_combobox = qtw.QComboBox()
        self.theme_combobox.addItems(["Light", "Dark"])
        self.theme_combobox.setCurrentIndex(1 if self.settings.darkmode else 0)
        self.theme_layout.addWidget(self.theme_label)
        self.theme_layout.addWidget(self.theme_combobox)
        self.layout.addLayout(self.theme_layout)

        # font size
        self.font_size_layout = qtw.QHBoxLayout()
        self.font_size_label = qtw.QLabel("Font Size:")
        self.font_size_spinbox = qtw.QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setValue(self.settings.font_size)
        self.font_size_layout.addWidget(self.font_size_label)
        self.font_size_layout.addWidget(self.font_size_spinbox)
        self.layout.addLayout(self.font_size_layout)

        # preferred width
        self.preferred_width_layout = qtw.QHBoxLayout()
        self.preferred_width_label = qtw.QLabel("Preferred Width:")
        self.preferred_width_spinbox = qtw.QSpinBox()
        self.preferred_width_spinbox.setRange(600, 4000)
        self.preferred_width_spinbox.setSingleStep(100)
        self.preferred_width_spinbox.setValue(self.settings.preferred_width)
        self.preferred_width_layout.addWidget(self.preferred_width_label)
        self.preferred_width_layout.addWidget(self.preferred_width_spinbox)
        self.layout.addLayout(self.preferred_width_layout)

        # preferred height
        self.preferred_height_layout = qtw.QHBoxLayout()
        self.preferred_height_label = qtw.QLabel("Preferred Height:")
        self.preferred_height_spinbox = qtw.QSpinBox()
        self.preferred_height_spinbox.setRange(400, 2000)
        self.preferred_height_spinbox.setSingleStep(100)
        self.preferred_height_spinbox.setValue(self.settings.preferred_height)
        self.preferred_height_layout.addWidget(self.preferred_height_label)
        self.preferred_height_layout.addWidget(self.preferred_height_spinbox)
        self.layout.addLayout(self.preferred_height_layout)

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

    def reset_settings(self):
        self.theme_combobox.setCurrentIndex(
            1 if self.settings.get_default("darkmode") else 0
        )
        self.font_size_spinbox.setValue(self.settings.get_default("font_size"))
        self.preferred_width_spinbox.setValue(
            self.settings.get_default("preferred_width")
        )
        self.preferred_height_spinbox.setValue(
            self.settings.get_default("preferred_height")
        )

    def accept(self):
        self.settings.darkmode = bool(self.theme_combobox.currentIndex())
        self.settings.font_size = self.font_size_spinbox.value()
        self.settings.preferred_width = self.preferred_width_spinbox.value()
        self.settings.preferred_height = self.preferred_height_spinbox.value()
        super().accept()

    def reject(self):
        super().reject()
