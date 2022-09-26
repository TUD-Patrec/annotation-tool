import os
import logging
import sys
import ctypes
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
from sys import platform

from src.main_controller import main
from src.utility import filehandler


def get_application_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
        print(os.path.realpath(__file__))
        print(os.path.dirname(__file__))
    else:
        raise RuntimeError('Could not determine the path to this document')
    return application_path
    
    
def enable_high_dpi_scaling():

    # adjust scaling to high dpi monitors
    if hasattr(qtc.Qt, 'AA_EnableHighDpiScaling'):
        qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(qtc.Qt, 'AA_UseHighDpiPixmaps'):
        qtw.QApplication.setAttribute(qtc.Qt.AA_UseHighDpiPixmaps, True)
    
    # Adjust scaling for windows 
    if platform == "win32":
        # Query DPI Awareness (Windows 10 and 8)
        #awareness = ctypes.c_int()
        #errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        # print( awareness.value)
        
        # Set DPI Awareness  (Windows 10 and 8)
        PROCESS_DPI_UNAWARE = 0
        PROCESS_SYSTEM_DPI_AWARE = 1
        PROCESS_PER_MONITOR_DPI_AWARE = 2
        errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_DPI_UNAWARE)
        if errorCode == 0:
            logging.info('Process runs DPI unaware')
    
    
    
    
if __name__ == '__main__':
    application_path = get_application_path()
      
    # Injecting root_path
    paths = filehandler.Paths.instance()
    paths.root = application_path
    
    # Init Folders and logger
    filehandler.init_folder_structure()
    filehandler.init_logger()
    
    logging.info('Running relative to {}'.format(application_path))
        
    enable_high_dpi_scaling()
        
    main()
    