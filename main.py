import ctypes
import logging
import os
import sys
from sys import platform
import warnings

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from src.main_controller import main
from src.settings import settings
from src.utility import filehandler

warnings.filterwarnings("ignore", category=UserWarning)


def get_application_path():
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.split(os.path.realpath(__file__))[0]
    else:
        raise RuntimeError("Could not get the path of this script")
    return application_path


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def enable_high_dpi_scaling():

    # adjust scaling to high dpi monitors
    if hasattr(qtc.Qt, "AA_EnableHighDpiScaling"):
        qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(qtc.Qt, "AA_UseHighDpiPixmaps"):
        qtw.QApplication.setAttribute(qtc.Qt.AA_UseHighDpiPixmaps, True)

    # Adjust scaling for windows
    if platform == "win32":
        # Query DPI Awareness (Windows 10 and 8)
        # awareness = ctypes.c_int()
        # tmp = ctypes.windll.shcore
        # errorCode = tmp.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        # print( awareness.value)

        # Set DPI Awareness  (Windows 10 and 8)
        PROCESS_DPI_UNAWARE = 0
        # PROCESS_SYSTEM_DPI_AWARE = 1
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_DPI_UNAWARE)
        if errorCode == 0:
            logging.info("Running DPI-unaware")


def start():
    filehandler.init_logger()
    # application_path = get_application_path()
    # logging.info("Running relative to {}".format(application_path))

    if settings.high_dpi_scaling:
        enable_high_dpi_scaling()

    main()


if __name__ == "__main__":
    start()
