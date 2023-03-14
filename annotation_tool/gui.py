import enum
from functools import partial

import PyQt6.QtCore as qtc
import PyQt6.QtGui as qtg
import PyQt6.QtWidgets as qtw

from annotation_tool.annotation.modes import AnnotationMode
from annotation_tool.dialogs.annotation_list import GlobalStatesDialog
from annotation_tool.settings import settings
from annotation_tool.user_actions import (
    get_annotation_actions,
    get_edit_actions,
    get_replay_actions,
    get_shortcut,
)

from . import __application_name__, __version__
from .data_model.annotation import Annotation
from .dialogs.dialog_manager import DialogManager
from .dialogs.edit_datasets import QEditDatasets
from .dialogs.import_annotation_dialog import ImportAnnotationDialog
from .dialogs.load_annotation_dialog import LoadAnnotationDialog
from .dialogs.local_files import LocalFilesDialog
from .dialogs.network_list import NetworksDialog
from .dialogs.new_annotation_dialog import NewAnnotationDialog
from .dialogs.settings_dialog import SettingsDialog
from .utility.resources import *  # noqa: F401, F403


class LayoutPosition(enum.Enum):
    TOP_LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_MIDDLE = 4


class GUI(qtw.QMainWindow, DialogManager):
    load_annotation = qtc.pyqtSignal(Annotation)
    save_pressed = qtc.pyqtSignal()
    exit_pressed = qtc.pyqtSignal()
    settings_changed = qtc.pyqtSignal()
    annotation_mode_changed = qtc.pyqtSignal(AnnotationMode)
    user_action = qtc.pyqtSignal(enum.Enum)

    def __init__(self, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)

        self.current_mode = AnnotationMode.MANUAL

        self.resize(settings.preferred_width, settings.preferred_height)
        self.setWindowTitle(
            "{} v{}".format(__application_name__.replace("_", " "), __version__)
        )
        self.setWindowIcon(qtg.QIcon(qtg.QPixmap(":/icon.png")))

        self.main_widget = qtw.QWidget()
        self.setCentralWidget(self.main_widget)

        self.widgets = dict()
        for layout_pos in LayoutPosition:
            self.widgets[layout_pos] = qtw.QWidget()

        self.grid = qtw.QGridLayout()

        self.main_widget.setLayout(self.grid)

        self.grid.addWidget(self.widgets[LayoutPosition.TOP_LEFT], 0, 0)
        self.grid.addWidget(self.widgets[LayoutPosition.MIDDLE], 0, 1)
        self.grid.addWidget(self.widgets[LayoutPosition.RIGHT], 0, 2, 2, 1)

        self.grid.addWidget(self.widgets[LayoutPosition.BOTTOM_LEFT], 1, 0)
        self.grid.addWidget(
            self.widgets[LayoutPosition.BOTTOM_MIDDLE],
            1,
            1,
            alignment=qtc.Qt.AlignmentFlag.AlignBottom,
        )

        self.grid.setColumnStretch(1, 1)

        # Menu Bar
        self.make_menu_bar()

        self.statusBar().show()

        # showing Main-Frame
        self.show()

    def write_to_statusbar(self, txt):
        self.statusBar().showMessage(str(txt), 2500)

    def make_menu_bar(self):
        self.file_menu()
        self.annotation_menu = self.menuBar().addMenu("&Annotation")
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.replay_menu = self.menuBar().addMenu("&Replay")
        self.update_flex_menus()
        self.annotation_mode_menu()
        self.settings_menu()

    def update_flex_menus(self):
        if not hasattr(self, "flex_actions"):
            self.flex_actions = {}
        self.build_flex_menu(self.annotation_menu, get_annotation_actions)
        self.build_flex_menu(self.edit_menu, get_edit_actions)
        self.build_flex_menu(self.replay_menu, get_replay_actions)

    def build_flex_menu(self, menu, get_function):
        menu.clear()
        for action in get_function(self.current_mode):
            shortcut = get_shortcut(action)

            self.flex_actions[action.name] = action

            fun = partial(self.emit_action, action)

            action_name = action.name.lower()
            action_name = action_name.replace("_", " ")
            action_name = action_name.replace("or", "/")
            action_name = action_name.replace("and", "&&")
            # capitalize every word
            action_name = " ".join(
                [word.capitalize() for word in action_name.split(" ")]
            )

            if shortcut is not None:
                menu.addAction(
                    action_name,
                    shortcut,
                    fun,
                )
            else:
                menu.addAction(
                    action_name,
                    fun,
                )

    def emit_action(self, action):
        self.user_action.emit(action)

    def settings_menu(self):
        menu = self.menuBar()
        options_menu = menu.addMenu("&Options")
        options_menu.addAction("About", self.open_about_dialog)
        options_menu.addAction(
            "Settings",
            self.open_settings,
        )
        options_menu.addAction("Local Files", self.open_local_files)

    def file_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(
            "New", qtg.QKeySequence.StandardKey.New, self.create_new_annotation
        )

        file_menu.addAction(
            "Open", qtg.QKeySequence.StandardKey.Open, self.load_existing_annotation
        )

        file_menu.addAction(
            "Save", qtg.QKeySequence.StandardKey.Save, self.save_pressed
        )

        file_menu.addAction("Annotations", self.list_annotations)

        file_menu.addAction("Datasets", self.edit_datasets)

        file_menu.addAction(
            "Networks",
            self.open_networks,
        )

        file_menu.addAction("Import", self.import_annotations)

        file_menu.addAction("Exit", qtg.QKeySequence.StandardKey.Close, self._exit)

    def annotation_mode_menu(self):
        menu = self.menuBar()

        self._annotation_mode_idx = 0

        annotation_menu = menu.addMenu("&Annotation Mode")

        ag = qtg.QActionGroup(self)
        ag.setExclusive(True)

        a = ag.addAction(qtg.QAction("Manual Annotation", self))
        a.setCheckable(True)
        a.setChecked(True)
        a.toggled.connect(lambda: self.update_annotation_mode(AnnotationMode.MANUAL))
        annotation_menu.addAction(a)

        a = ag.addAction(qtg.QAction("Retrieval Mode", self))
        a.setCheckable(True)
        a.toggled.connect(lambda: self.update_annotation_mode(AnnotationMode.RETRIEVAL))
        annotation_menu.addAction(a)

    def update_annotation_mode(self, new_mode):
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.update_flex_menus()
            self.annotation_mode_changed.emit(new_mode)

    def open_settings(self):
        dialog = SettingsDialog()
        dialog.window_size_changed.connect(self.resize)
        dialog.settings_changed.connect(self.settings_changed)
        self.open_dialog(dialog)

    def open_networks(self):
        dialog = NetworksDialog()
        self.open_dialog(dialog)

    def open_about_dialog(self):
        pass  # TODO

    def open_local_files(self):
        dialog = LocalFilesDialog()
        self.open_dialog(dialog)

    def create_new_annotation(self):
        dialog = NewAnnotationDialog()
        dialog.load_annotation.connect(self.load_annotation)
        self.open_dialog(dialog)
        self.save_pressed.emit()

    def load_existing_annotation(self):
        dialog = LoadAnnotationDialog()
        dialog.load_annotation.connect(self.load_annotation)
        self.open_dialog(dialog)
        self.save_pressed.emit()

    def list_annotations(self):
        dialog = GlobalStatesDialog()
        self.open_dialog(dialog)

    def edit_datasets(self):
        dialog = QEditDatasets()
        self.open_dialog(dialog)

    def import_annotations(self):
        dialog = ImportAnnotationDialog()
        self.open_dialog(dialog)

    @qtc.pyqtSlot(qtw.QWidget, LayoutPosition)
    def set_widget(self, widget, layout_position):
        old_widget = self.widgets[layout_position]

        if widget is None:
            widget = qtw.QWidget()

        # store new widget into dict
        self.widgets[layout_position] = widget

        self.grid.replaceWidget(old_widget, widget)

        old_widget.setParent(None)
        old_widget.deleteLater()

    @qtc.pyqtSlot(qtg.QCloseEvent)
    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self._exit()

    def _exit(self):
        self.close_dialog()
        self.exit_pressed.emit()
