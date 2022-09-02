import os
import logging
import sys

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from src.main_controller import main
from src.utility import filehandler


def get_application_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    return application_path
    
    
def enable_high_dpi_scaling():
    # adjust scaling to high dpi monitors
    if hasattr(qtc.Qt, 'AA_EnableHighDpiScaling'):
        qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(qtc.Qt, 'AA_UseHighDpiPixmaps'):
        qtw.QApplication.setAttribute(qtc.Qt.AA_UseHighDpiPixmaps, True)
    
if __name__ == '__main__':
    application_path = get_application_path()
      
    enable_high_dpi_scaling()
      
    # Injecting root_path
    paths = filehandler.Paths.instance()
    paths.root = application_path
    
    # Init Folders and logger
    filehandler.init_folder_structure()
    filehandler.init_logger()
    
    logging.info('Running relative to {}'.format(application_path))
        
    main()