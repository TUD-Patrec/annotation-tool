import os
import logging
import pickle
import numpy as np
import json
import cv2
import math

from dataclasses import dataclass, field
from .decorators import Singleton
from ..data_classes.singletons import Settings

@Singleton
@dataclass()
class Paths:
    _root: str = field(init=False, default=None)
    _local_storage: str = field(init=False, default='__local__storage__')
    _annotations: str = field(init=False, default='annotations')
    _datasets: str = field(init=False, default='dataset_schemes')
    _networks: str = field(init=False, default='networks')
    _resources: str = field(init=False, default='resources')
    _config: str = field(init=False, default='config.json')
        
    @property        
    def root(self):
        return self._root
    
    @root.setter
    def root(self, path):
        if self._root is None and os.path.isdir(path):
           self._root = path
    
    @property
    def local_storage(self):
        return os.path.join(self.root, self._local_storage)
    
    @property
    def annotations(self):
        return os.path.join(self.local_storage, self._annotations)
    
    @property
    def datasets(self):
        return os.path.join(self.local_storage, self._datasets)
    
    @property
    def networks(self):
        return os.path.join(self.local_storage, self._networks)
    
    @property
    def resources(self):
        return os.path.join(self.local_storage, self._resources)
    
    @property
    def config(self):
        return os.path.join(self.local_storage, self._config)
    
       
def is_non_zero_file(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def footprint_of_file(path):
    with open(path, "rb") as f:
        x = f.read(2 ** 20)
    x = int.from_bytes(x, byteorder='big', signed=True)
    x %= 2 ** 32
    logging.info('hash = {}'.format(x))
    return x


def read_json(path):
    if is_non_zero_file(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        logging.warning('FILE {} is empty.'.format(path))
        return None


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def csv_to_numpy(path, dtype=np.float64):
    if is_non_zero_file(path):
        return np.genfromtxt(path, delimiter=',', dtype=dtype)
    else:
        logging.warning('FILE {} is empty.'.format(path))
        return None


def numpy_to_csv(path, data):
    np.savetxt(path, data, fmt='%d', delimiter=',')


def write_pickle(path, data):
    with open (path, 'wb') as f:
            pickle.dump(data, f)


def read_pickle(path):
    with open (path, 'rb') as f:
        data = pickle.load(f)        
    return data


def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def remove_file(path):
    if os.path.isfile(path):
        os.remove(path)
    
         
def path_to_filename(path):
    if os.path.isfile(path):
        filename = os.path.split(path)[-1]
        return filename.split('.')[0]


def path_to_dirname(path):
    if os.path.isdir(path):
        dirname = os.path.split(path)[-1]
        return dirname
    

def meta_data(path):
    if is_non_zero_file(path):
        if path.split('.')[-1] == 'csv':
            return meta_data_of_mocap(path)
        if path.split('.')[-1] in ['mp4', 'avi']:
            return meta_data_of_video(path)
    else:
        raise FileNotFoundError


def meta_data_of_mocap(path):
    logging.info('meta_mocap Start')
    
    mocap = csv_to_numpy(path)
    frame_count = mocap.shape[0]
    fps = Settings.instance().refresh_rate
    
    logging.info('meta_mocap End')
    
    return 1000 * int(frame_count / fps), frame_count, fps 
    

def meta_data_of_video(path):
    video = cv2.VideoCapture(path)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_rate = video.get(cv2.CAP_PROP_FPS)
    duration = frame_count / frame_rate
    lower, upper = math.floor(duration), math.ceil(duration)
    
    d_lower = abs(lower * frame_rate - frame_count)
    d_upper = abs(upper * frame_rate - frame_count)
    
    # picking the better choice
    if d_lower < d_upper:
        duration = 1000 * lower
    else:
        duration = 1000 * upper
        
    return duration, frame_count, frame_rate


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


def logging_config():
    return {
        'version': 1, 
        'disable_existing_loggers': True, 
        'formatters': {
            'screen': {
                'format': '[%(asctime)s] [%(levelname)s] [%(filename)s():%(lineno)s] - %(message)s', 
                'datefmt': '%Y-%m-%d %H:%M:%S'
                }, 
            'full': {
                'format': '[%(asctime)s] [%(levelname)s] - %(message)s', 
                'datefmt': '%Y-%m-%d %H:%M:%S'
                        }
            }, 
        'handlers': {
            'screen_handler': {
                'level': 'WARNING',
                'formatter': 'screen', 
                'class': 'logging.StreamHandler', 
                'stream': 'ext://sys.stdout'
                }
            },
        'loggers': {
            '': {
                'handlers': ['screen_handler'],
                'level': 'DEBUG', 
                'propagate': False
                }
            }
        }
    
    
def init_logger():
    log_config_dict = logging_config()
    log_config_dict['handlers']['screen_handler']['level'] = 'DEBUG' if Settings.instance().debugging_mode else 'WARNING'
    logging.config.dictConfig(log_config_dict)


# TODO
def clean_folders():
    paths: Paths = Paths.instance()
    pass

def init_folder_structure():
    clean_folders()
    
    paths = Paths.instance()
    
    create_dir(paths.local_storage)
    create_dir(paths.annotations)
    create_dir(paths.datasets)
    create_dir(paths.networks)
    create_dir(paths.resources)