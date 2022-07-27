import os
import logging
import sys
from src.anno_tool import main
from src.data_classes.singletons import Paths
from src.util.util import init_folder_structure, init_logger


def get_application_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    return application_path
    
    
if __name__ == '__main__':
    application_path = get_application_path()
        
    # Injecting root_path, so the singleton can work properly
    paths = Paths.instance()
    paths.root = application_path
    
    # Init Folders and logger
    init_folder_structure()
    init_logger()
    
    logging.info('Running relative to {}'.format(application_path))
    
    main()