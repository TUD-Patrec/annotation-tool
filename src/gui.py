import enum
import logging

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

from src.dataclasses.settings import Settings

from .dataclasses.globalstate import GlobalState
from .dialogs.dialog_manager import DialogManager
from .dialogs.edit_datasets import QEditDatasets
from .dialogs.export_annotation_dialog import QExportAnnotationDialog
from .dialogs.load_annotation_dialog import QLoadExistingAnnotationDialog
from .dialogs.new_annotation_dialog import QNewAnnotationDialog
from .dialogs.settings_dialog import SettingsDialog


class LayoutPosition(enum.Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class GUI(qtw.QMainWindow, DialogManager):
    load_annotation = qtc.pyqtSignal(GlobalState)
    save_pressed = qtc.pyqtSignal()
    exit_pressed = qtc.pyqtSignal()
    play_pause_pressed = qtc.pyqtSignal()
    skip_frames = qtc.pyqtSignal(bool, bool)
    cut_pressed = qtc.pyqtSignal()
    cut_and_annotate_pressed = qtc.pyqtSignal()
    merge_left_pressed = qtc.pyqtSignal()
    merge_right_pressed = qtc.pyqtSignal()
    annotate_pressed = qtc.pyqtSignal()
    increase_speed_pressed = qtc.pyqtSignal()
    decrease_speed_pressed = qtc.pyqtSignal()
    reset_pressed = qtc.pyqtSignal()
    undo_pressed = qtc.pyqtSignal()
    redo_pressed = qtc.pyqtSignal()
    merge_adjacent_pressed = qtc.pyqtSignal()
    settings_changed = qtc.pyqtSignal()
    use_manual_annotation = qtc.pyqtSignal()
    use_retrieval_mode = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(GUI, self).__init__(*args, **kwargs)

        # window setup
        settings = Settings.instance()

        self.resize(settings.window_x, settings.window_y)
        logging.info(self.size())
        self.setWindowTitle("Annotation Tool")
        # self.setWindowIcon()

        self.main_widget = qtw.QWidget()
        self.setCentralWidget(self.main_widget)

        self.widgets = dict()
        for layout_pos in LayoutPosition:
            self.widgets[layout_pos] = qtw.QWidget()

        self.vbox = qtw.QVBoxLayout()
        self.main_widget.setLayout(self.vbox)

        self.top_hbox = qtw.QHBoxLayout()
        self.top_hbox.addWidget(
            self.widgets[LayoutPosition.LEFT], alignment=qtc.Qt.AlignLeft
        )
        self.top_hbox.addWidget(self.widgets[LayoutPosition.MIDDLE], stretch=1)
        self.top_hbox.addWidget(
            self.widgets[LayoutPosition.RIGHT], alignment=qtc.Qt.AlignRight
        )

        self.bottom_hbox = qtw.QHBoxLayout()
        self.bottom_hbox.addWidget(
            self.widgets[LayoutPosition.BOTTOM_LEFT], alignment=qtc.Qt.AlignLeft
        )
        self.bottom_hbox.addWidget(
            self.widgets[LayoutPosition.BOTTOM_RIGHT],
            stretch=1,
            alignment=qtc.Qt.AlignBottom,
        )

        self.vbox.addLayout(self.top_hbox, stretch=1)
        self.vbox.addLayout(self.bottom_hbox)

        # Menu Bar
        self.make_menu_bar()

        self.statusBar().show()

        # showing Main-Frame
        self.show()

    def write_to_statusbar(self, txt):
        self.statusBar().showMessage(str(txt))

    def make_menu_bar(self):
        self.file_menu()
        self.video_menu()
        self.edit_menu()
        self.settings_menu()
        self.annotation_mode_menu()

    def video_menu(self):
        menu = self.menuBar()
        video_menu = menu.addMenu("&Video")

        video_menu.addAction(
            "Play/Pause", self.play_pause_pressed, qtg.QKeySequence(qtc.Qt.Key_Space)
        )

        video_menu.addAction(
            "Next Frame",
            lambda: self.skip_frames.emit(True, False),
            qtg.QKeySequence(qtc.Qt.Key_Right),
        )

        video_menu.addAction(
            "Last Frame",
            lambda: self.skip_frames.emit(False, False),
            qtg.QKeySequence(qtc.Qt.Key_Left),
        )

        video_menu.addAction(
            "Skip +100 Frames",
            lambda: self.skip_frames.emit(True, True),
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_Right),
        )

        video_menu.addAction(
            "Skip -100 Frames",
            lambda: self.skip_frames.emit(False, True),
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_Left),
        )

        video_menu.addAction(
            "Increase replay speed", lambda: self.increase_speed_pressed.emit()
        )

        video_menu.addAction(
            "Decrease replay speed", lambda: self.decrease_speed_pressed.emit()
        )

    def edit_menu(self):
        menu = self.menuBar()
        edit_menu = menu.addMenu("&Edit")

        edit_menu.addAction(
            "Annotate",
            self.annotate_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_A),
        )

        edit_menu.addAction(
            "Cut", self.cut_pressed, qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_C)
        )

        edit_menu.addAction(
            "Cut + Annotate",
            self.cut_and_annotate_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_X),
        )

        edit_menu.addAction(
            "Merge Left",
            self.merge_left_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_L),
        )

        edit_menu.addAction(
            "Merge Right",
            self.merge_right_pressed,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_R),
        )

        edit_menu.addAction("Undo", self.undo_pressed, qtg.QKeySequence.Undo)

        edit_menu.addAction("Redo", self.redo_pressed, qtg.QKeySequence.Redo)

    def settings_menu(self):
        menu = self.menuBar()
        settings_menu = menu.addMenu("&Options")
        settings_menu.addAction(
            "Options",
            self.open_settings,
        )

    def file_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction("New", self.create_new_annotation, qtg.QKeySequence.New)

        file_menu.addAction(
            "Open", self.load_existing_annotation, qtg.QKeySequence.Open
        )

        file_menu.addAction("Save", self.save_pressed, qtg.QKeySequence.Save)

        file_menu.addAction(
            "Export Annotation",
            self.export_annotation,
            qtg.QKeySequence(qtc.Qt.CTRL + qtc.Qt.Key_E),
        )

        file_menu.addAction("Edit Datasets", self.edit_datasets)

        file_menu.addAction("Exit", self._exit, qtg.QKeySequence.Close)

    def annotation_mode_menu(self):
        menu = self.menuBar()

        self._annotation_mode_idx = 0

        annotation_menu = menu.addMenu("&Annotation Mode")

        ag = qtw.QActionGroup(self)
        ag.setExclusive(True)

        a = ag.addAction(qtw.QAction("Manual Annotation", self, checkable=True))
        a.setChecked(True)
        a.toggled.connect(self.manual_anotation_toggled)
        annotation_menu.addAction(a)

        a = ag.addAction(qtw.QAction("Retrieval Mode", self, checkable=True))
        a.toggled.connect(self.retrievel_mode_toggled)
        annotation_menu.addAction(a)

    def manual_anotation_toggled(self, active):
        if active:
            self.use_manual_annotation.emit()

    def retrievel_mode_toggled(self, active):
        if active:
            self.use_retrieval_mode.emit()

    def open_settings(self):
        dialog = SettingsDialog()
        dialog.window_size_changed.connect(self.resize)
        dialog.settings_changed.connect(self.settings_changed)
        self.open_dialog(dialog)

    def create_new_annotation(self):
        dialog = QNewAnnotationDialog()
        dialog.load_annotation.connect(self.load_annotation)
        self.open_dialog(dialog)
        self.save_pressed.emit()

    def load_existing_annotation(self):
        dialog = QLoadExistingAnnotationDialog()
        dialog.load_annotation.connect(self.load_annotation)
        self.open_dialog(dialog)
        self.save_pressed.emit()

    def export_annotation(self):
        dialog = QExportAnnotationDialog()
        self.open_dialog(dialog)
        self.save_pressed.emit()

    def edit_datasets(self):
        dialog = QEditDatasets()
        self.open_dialog(dialog)

    @qtc.pyqtSlot(qtw.QWidget, LayoutPosition)
    def set_widget(self, widget, layout_position):
        old_widget = self.widgets[layout_position]

        if widget is None:
            widget = qtw.QWidget()

        # store new widget into dict
        self.widgets[layout_position] = widget

        if layout_position in [LayoutPosition.BOTTOM_RIGHT, LayoutPosition.BOTTOM_LEFT]:
            self.bottom_hbox.replaceWidget(old_widget, widget)
        else:
            self.top_hbox.replaceWidget(old_widget, widget)

        old_widget.setParent(None)
        old_widget.deleteLater()

    @qtc.pyqtSlot()
    def cleaned_up(self):
        self.close()

    @qtc.pyqtSlot(qtg.QCloseEvent)
    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self._exit()

    def _exit(self):
        self.close_dialog()
        self.exit_pressed.emit()
