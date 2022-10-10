import PyQt5.QtCore as qtc


class DialogManager:
    def __init__(self):
        self.__open_dialog__ = None

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
            self.__refocus_dialog__()

    def __free_dialog__(self):
        self.__open_dialog__
        self.__open_dialog__.deleteLater()
        self.__open_dialog__ = None
