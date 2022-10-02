import PyQt5.QtCore as qtc

__open_dialog__ = None


def __refocus_dialog__():
    # this will remove minimized status
    # and restore window with keeping maximized/normal state
    global __open_dialog__
    __open_dialog__.setWindowState(
        __open_dialog__.windowState() & ~qtc.Qt.WindowMinimized | qtc.Qt.WindowActive
    )

    # this will activate the window
    __open_dialog__.activateWindow()


def open_dialog(dialog):
    global __open_dialog__
    if __open_dialog__ is None:
        __open_dialog__ = dialog
        dialog.open()
        dialog.finished.connect(__free_dialog__)
    else:
        __refocus_dialog__()


def __free_dialog__():
    global __open_dialog__
    __open_dialog__.deleteLater()
    __open_dialog__ = None
