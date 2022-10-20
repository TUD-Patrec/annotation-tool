import enum

import PyQt5.QtCore as qtc


class DialogOpenStrategy(enum.Enum):
    REFOCUS = 0
    SUBSTITUTE = 1


class DialogManager:
    def __init__(self):
        self.__open_dialog__ = None
        self.strategy = DialogOpenStrategy.SUBSTITUTE

    def __refocus_dialog__(self):
        # this will remove minimized status
        # and restore window with keeping maximized/normal state
        self.__open_dialog__
        self.__open_dialog__.setWindowState(
            self.__open_dialog__.windowState() & ~qtc.Qt.WindowMinimized
            | qtc.Qt.WindowActive
        )

        # this will activate the window
        self.__open_dialog__.activateWindow()

    def open_dialog(self, dialog):
        if self.__open_dialog__ is None:
            self.__open_dialog__ = dialog
            dialog.open()
            dialog.finished.connect(self.__free_dialog__)
        else:
            if self.strategy == DialogOpenStrategy.SUBSTITUTE:
                self.__open_dialog__.close()  # Close current dialog
                self.open_dialog(dialog)  # Recurse
            elif self.strategy == DialogOpenStrategy.REFOCUS:
                self.__refocus_dialog__()

    def close_dialog(self):
        if self.__open_dialog__ is not None:
            self.__open_dialog__.close()

    def __free_dialog__(self):
        self.__open_dialog__
        self.__open_dialog__.deleteLater()
        self.__open_dialog__ = None
