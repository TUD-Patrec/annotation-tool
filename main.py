import ctypes
from sys import platform
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


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
