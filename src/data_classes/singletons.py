from dataclasses import dataclass, field, fields
import os
import logging
from ..util import functions, util
from distinctipy import distinctipy
import PyQt5.QtGui as qtg
import random

class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
@dataclass()
class ColorMapper:
    _scheme: list = field(init=False)
    _color_map: list = field(init=False)
    
    def __init__(self) -> None:
        random.seed(42)
        self._color_map = distinctipy.get_colors(50, n_attempts=250)
        
    @property
    def scheme(self):
        return self._scheme
    
    @scheme.setter
    def scheme(self, value):
        if type(value) != list:
            ValueError
        else:
            self._scheme = value
    
    def annotation_to_color(self, annotation):
        if annotation is None:
            raise ValueError
        elif not bool(annotation):
            raise ValueError('Cant be empty')
        else:
            group_name = self.scheme[0][0]
            group_elements = self.scheme[0][1]
            first_group = [annotation[group_name][label_name] for label_name in group_elements]
            
            # bin_array -> number
            x = ""
            for idx, value in enumerate(first_group, 1):
                if value:
                    x += str(idx)
            
            x = int(x)
            x %= len(self._color_map)
            
            r,g,b = self._color_map[x]
            r, g, b = r * 255, g * 255, b * 255
            color = qtg.QColor(r,g,b)
            color.setAlpha(127)
            
            return color


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
    
    

@Singleton
@dataclass()
class Settings:
    _annotator_id: int = field(init=False, default=0)
    _language: int = field(init=False, default=0)
    _debugging_mode: bool = field(init=False, default=False)
    _window_x: int = field(init=False, default=1600)
    _window_y: int = field(init=False, default=900)
    _dark_mode: bool = field(init=False, default=False)
    _tiny_font: int = field(init=False, default=6)
    _small_font: int = field(init=False, default=8)
    _medium_font: int = field(init=False, default=10)
    _large_font: int = field(init=False, default=12)
    _mocap_grid: bool = field(init=False, default=True)
    _show_millisecs: bool = field(init=False, default=False)
    _small_skip: int = field(init=False, default=1)
    _big_skip: int = field(init=False, default=100)
    
    
    def __post_init__(self):
        paths = Paths.instance()
        if not util.is_non_zero_file(paths.config):
            self.to_disk()
        else:
            self.from_disk()
    
    def window_extrema(self):
        return 1280, 720, 5000, 3000
    
    @property
    def annotator_id(self):
        return self._annotator_id
    
    @annotator_id.setter
    def annotator_id(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._annotator_id = value
    
    @property
    def language(self):
        return self._language
    
    @language.setter
    def language(self, value):
        if type(value) != int or value not in [0,1]:
            raise ValueError
        else:
            self._language = value
    
    @property
    def debugging_mode(self):
        return self._debugging_mode
    
    @debugging_mode.setter
    def debugging_mode(self, value):
        if type(value) != bool:
            raise ValueError
        else:
            self._debugging_mode = value
    
    @property    
    def window_x(self):
        return self._window_x

    @window_x.setter
    def window_x(self, value):
        if type(value) != int:
            raise ValueError
        else:
            x_min, y_min, x_max, y_max = self.window_extrema()
            self._window_x = max(min(value, x_max), x_min)
        
    @property    
    def window_y(self):
        return self._window_y

    @window_y.setter
    def window_y(self, value):
        if type(value) != int:
            raise ValueError
        else:
            x_min, y_min, x_max, y_max = self.window_extrema()
            self._window_y = max(min(value, y_max), y_min)
    
    @property
    def darkmode(self):
        return self._dark_mode
    
    @darkmode.setter
    def darkmode(self, value):
        if type(value) != bool:
            raise ValueError
        else:
            self._dark_mode = value
            
    @property
    def tiny_font(self):
        return self._tiny_font
    
    @tiny_font.setter
    def tiny_font(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._tiny_font = min(max(6, value), 30)
            
    @property
    def small_font(self):
        return self._small_font
    
    @small_font.setter
    def small_font(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._small_font = min(max(6, value), 30)        
            
    @property
    def medium_font(self):
        return self._medium_font
    
    @medium_font.setter
    def medium_font(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._medium_font = min(max(6, value), 30)        
            
    @property
    def large_font(self):
        return self._large_font
    
    @large_font.setter
    def large_font(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._large_font = min(max(6, value), 30)

    @property
    def mocap_grid(self):
        return self._mocap_grid
    
    @mocap_grid.setter
    def mocap_grid(self, value):
        if type(value) != bool:
            raise ValueError
        else:
            self._mocap_grid = value
            
    @property
    def show_millisecs(self):
        return self._show_millisecs
    
    @show_millisecs.setter
    def show_millisecs(self, value):
        if type(value) != bool:
            raise ValueError
        else:
            self._show_millisecs = value
            
    @property
    def small_skip(self):
        return self._small_skip
    
    @small_skip.setter
    def small_skip(self, value):
        if type(value) != int or value < 1:
            raise ValueError
        else:
            self._small_skip = value
            
    @property
    def big_skip(self):
        return self._big_skip
    
    @big_skip.setter
    def big_skip(self, value):
        if type(value) != int or value < 1:
            raise ValueError
        else:
            self._big_skip = value
        
    def reset(self):
        for field in fields(self):
            setattr(self, field.name, field.default) 
        
    def from_disk(self):
        paths = Paths.instance()
        d = util.read_json(paths.config)
        self.from_dict(d)
            
    def to_disk(self):
        paths = Paths.instance()
        d = self.as_dict()
        util.write_json(paths.config, d)
    
    def from_dict(self, d):
        for field in fields(self):
            logging.info('{} <- {}'.format(field.name, d[field.name]))
            setattr(self, field.name, d[field.name])
    
    def as_dict(self):
        return dict((field.name, getattr(self, field.name)) for field in fields(self))
        

@Singleton
class FrameTimeMapper():
    def __init__(self) -> None:
        self.use_time = Settings.instance().show_millisecs
        self.n_frames = 1
        self.millisecs = 1
        self._frame_to_ms, self._ms_to_frame = functions.scale_functions(1,1, True)
        
         
    def settings_changed(self):
        self.use_time = Settings.instance().show_millisecs
        
    def set_annotation(self, n_frames, millisecs):
        self.n_frames = n_frames
        self.millisecs = millisecs
        logging.info('{}, {}'.format(n_frames, millisecs))
        self._frame_to_ms, self._ms_to_frame = functions.scale_functions(self.n_frames, self.millisecs, True)
        
    def frame_repr(self, frame):
        if self.use_time:
            millisecs = self._frame_to_ms(frame)[0]
            return functions.ms_to_time_string(millisecs)
        else:
            return str(frame)
        
    def frame_to_ms(self, ms):
        return self._frame_to_ms(ms)[0]
    
    def ms_to_frame(self, frame):
        return self._ms_to_frame(frame)[0]