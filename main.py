import ctypes
import logging
import os
import sys
from sys import platform
import warnings

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


def apply_pixel_scaling():
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
        else:
            logging.warning("Could not set DPI-unaware")


def start():
    if platform == "win32":
        myappid = "annotation_tool_unique_app_id"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            myappid
        )  # update taskbar icon

    from annotation_tool.utility import filehandler

    filehandler.init_logger()

    from annotation_tool.main_controller import main

    main()


if __name__ == "__main__":
    start()
