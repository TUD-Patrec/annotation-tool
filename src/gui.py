import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import logging

from src.data_classes.settings import Settings
from .data_classes.globalstate import GlobalState
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.edit_datasets import QEditDatasets
from .dialogs.new_annotation_dialog import QNewAnnotationDialog
from .dialogs.load_annotation_dialog import QLoadExistingAnnotationDialog
from .dialogs.export_annotation_dialog import QExportAnnotationDialog


class GUI(qtw.QMainWindow):
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
        self.dialog = None
        settings = Settings.instance()

        self.resize(settings.window_x, settings.window_y)
        logging.info(self.size())
        self.setWindowTitle("Annotation Tool")
        # self.setWindowIcon()

        self.main_widget = qtw.QWidget()
        self.vbox = qtw.QVBoxLayout()
        self.hbox = qtw.QHBoxLayout()
        self.main_widget.setLayout(self.vbox)

        self.left_widget = qtw.QWidget()
        self.bottom_widget = qtw.QWidget()
        self.right_widget = qtw.QWidget()
        self.central_widget = qtw.QWidget()

        self.hbox.addWidget(self.left_widget, alignment=qtc.Qt.AlignLeft)
        self.hbox.addWidget(self.central_widget, stretch=1)
        self.hbox.addWidget(self.right_widget, alignment=qtc.Qt.AlignRight)

        self.vbox.addLayout(self.hbox, stretch=1)
        self.vbox.addWidget(self.bottom_widget)

        self.setCentralWidget(self.main_widget)

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
            logging.info("manual anno emit")
            self.use_manual_annotation.emit()

    def retrievel_mode_toggled(self, active):
        if active:
            logging.info("retrieval_backend emit")
            self.use_retrieval_mode.emit()

    def open_settings(self):
        if self.dialog is None:
            self.dialog = SettingsDialog()
            self.dialog.settings_changed.connect(self.settings_changed)
            self.dialog.window_size_changed.connect(self.resize)
            self.dialog.finished.connect(self.free_dialog)
            self.dialog.open()
        else:
            self.refocus_dialog()

    def create_new_annotation(self):
        if self.dialog is None:
            self.dialog = QNewAnnotationDialog()
            self.dialog.load_annotation.connect(self.load_annotation)
            self.dialog.finished.connect(self.free_dialog)
            self.dialog.open()
        else:
            self.refocus_dialog()

    def load_existing_annotation(self):
        if self.dialog is None:
            self.dialog = QLoadExistingAnnotationDialog()
            self.dialog.load_annotation.connect(self.load_annotation)
            self.dialog.finished.connect(self.free_dialog)
            self.dialog.open()
        else:
            self.refocus_dialog()

    def export_annotation(self):
        if self.dialog is None:
            self.dialog = QExportAnnotationDialog()
            self.dialog.finished.connect(self.free_dialog)
            self.dialog.open()
        else:
            self.refocus_dialog()

    def edit_datasets(self):
        if self.dialog is None:
            self.dialog = QEditDatasets()
            self.dialog.finished.connect(self.free_dialog)
            self.dialog.open()
        else:
            self.refocus_dialog()

    def refocus_dialog(self):
        # this will remove minimized status
        # and restore window with keeping maximized/normal state
        self.dialog.setWindowState(
            self.dialog.windowState() & ~qtc.Qt.WindowMinimized | qtc.Qt.WindowActive
        )

        # this will activate the window
        self.dialog.activateWindow()

    @qtc.pyqtSlot(int)
    def free_dialog(self, x):
        self.dialog.deleteLater()
        self.dialog = None

    def set_left_widget(self, widget):
        self.hbox.replaceWidget(self.left_widget, widget)
        self.left_widget.setParent(None)
        self.right_widget.deleteLater()
        self.left_widget = widget

    def set_central_widget(self, widget):
        self.hbox.replaceWidget(self.central_widget, widget)
        self.central_widget.setParent(None)
        self.right_widget.deleteLater()
        self.central_widget = widget
        self.central_widget.adjustSize()

    def set_right_widget(self, widget):
        self.hbox.replaceWidget(self.right_widget, widget)
        self.right_widget.setParent(None)
        self.right_widget.deleteLater()
        self.right_widget = widget

    def set_bottom_widget(self, widget):
        self.vbox.replaceWidget(self.bottom_widget, widget)
        self.bottom_widget.setParent(None)
        self.right_widget.deleteLater()
        self.bottom_widget = widget

    def cleaned_up(self):
        self.close()

    @qtc.pyqtSlot(qtg.QCloseEvent)
    def closeEvent(self, a0: qtg.QCloseEvent) -> None:
        self._exit()

    def _exit(self):
        if self.dialog:
            logging.info("Closing open dialog")
            self.dialog.close()
        self.exit_pressed.emit()
