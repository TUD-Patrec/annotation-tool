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


def test():
    from annotation_tool.utility import filehandler

    filehandler.init_logger()

    from annotation_tool.data_model.media_type import MediaType
    from annotation_tool.data_model.model import Model, create_model
    from annotation_tool.media_reader import set_fallback_fps
    from annotation_tool.network.controller import __run_network__

    mocap_file = r"C:\Users\Raphael\Desktop\L01_S14_R01.csv"
    network_file = r"C:\Users\Raphael\Desktop\traced_network.pt"

    set_fallback_fps(6)

    model = create_model(
        network_path=network_file,
        sampling_rate=100,
        media_type=MediaType.MOCAP,
        input_shape=(100, 132),
    )

    print(f"{model.output_shape = }")
    print(*Model.get_all(), sep="\n")

    sucessful_cases = [
        (0, 1),
        (0, 86),
        (100, 111),
        (23800, 23900),
        (23900, 23999),
        (0, 23999),
        (23998, 23999),
        (23999, 23999),
    ]

    for idx, (start, end) in enumerate(sucessful_cases):
        out = __run_network__(mocap_file, start, end)
        print(f"{idx = }: ({start}, {end}) -> {out.shape = }")

    non_sucessful_cases = [
        (-100, 56),
        (-1, 1),
        (-100, -1),
        (-100, 0),
        (0, -1),
        (5, 1),
        (5, -1),
        (24000, 23999),
        (24001, 24000),
        (0, 24000),
        (23900, 24000),
        (23900, 24001),
        (23999, 24000),
        (24000, 24100),
    ]

    for idx, (start, end) in enumerate(non_sucessful_cases):
        try:
            __run_network__(mocap_file, start, end)
        except AssertionError as e:
            print(f"{idx = }: ({start}, {end}) -> {e = }")
            continue

        raise Exception(f"{idx = }: ({start}, {end}) should have failed")

    Model.del_all()


if __name__ == "__main__":
    start()
    # test()
