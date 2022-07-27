import hashlib
import pickle
import numpy as np
import logging
import logging.config
import os
import cv2
import PIL
import json
import random
import PyQt5.QtGui as qtg
import numpy as np
import math
from ..data_classes.singletons import Paths, Settings

def footprint_of_file(path):
    with open(path, "rb") as f:
        x = f.read(2 ** 20)
    x = int.from_bytes(x, byteorder='big', signed=True)
    x %= 2 ** 32
    logging.info('hash = {}'.format(x))
    return x

def __generate_file_md5__(path, blocksize=2**20):
    m = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()

def generate_random_color(seed):
    random.seed(seed)
    color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
    return qtg.QColor(color)
      
def meta_data(path):
    if is_non_zero_file(path):
        if path.split('.')[-1] == 'csv':
            raise NotImplementedError
        if path.split('.')[-1] in ['mp4', 'avi']:
            return meta_data_of_video(path)
    else:
        raise FileNotFoundError

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

def ms_to_frames(ms, fps):
    return max(1, ms // fps)

def frames_to_ms(frames, fps):
    return frames * fps

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
    logging.getLogger(PIL.__name__).setLevel(logging.WARNING)
    
def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return path

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
    
def is_non_zero_file(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

def path_to_filename(path):
    if os.path.isfile(path):
        filename = os.path.split(path)[-1]
        return filename.split('.')[0]

def path_to_dirname(path):
    if os.path.isdir(path):
        dirname = os.path.split(path)[-1]
        return dirname

def get_current_user(root_path):
    user_path = os.path.join(root_path, 'users')
    users = []
    for file in os.listdir(user_path):
        user_file = os.path.join(user_path, file)
        if is_non_zero_file(user_file):
            users.append(read_json(user_file))
    
    assert 1 <= len(users) <= 2
    
    user = users[0]
    
    if len(users) == 2:
        if user['name'] == 'default_user':
            user = user[1]
            
    return user
        
def create_user(name = 'default_user', id = 0):
    usr = dict()
    usr['name'] = name
    usr['id']  = id
    
    return usr