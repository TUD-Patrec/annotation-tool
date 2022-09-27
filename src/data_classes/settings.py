import logging

from dataclasses import dataclass, field, fields
from src.utility import filehandler
from src.utility.decorators import Singleton


@Singleton
@dataclass()
class Settings:
    _annotator_id: int = field(init=False, default=0)
    _debugging_mode: bool = field(init=False, default=False)
    _window_x: int = field(init=False, default=1200)
    _window_y: int = field(init=False, default=700)
    _dark_mode: bool = field(init=False, default=False)
    _font: int = field(init=False, default=10)
    _refresh_rate: int = field(init=False, default=100)
    _show_millisecs: bool = field(init=False, default=False)
    _small_skip: int = field(init=False, default=1)
    _big_skip: int = field(init=False, default=100)

    def __post_init__(self):
        paths = filehandler.Paths.instance()
        if not filehandler.is_non_zero_file(paths.config):
            self.to_disk()
        else:
            self.from_disk()

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
            self._window_x = value

    @property
    def window_y(self):
        return self._window_y

    @window_y.setter
    def window_y(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._window_y = value

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
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._font = min(max(6, value), 30)

    @property
    def refresh_rate(self):
        return self._refresh_rate

    @refresh_rate.setter
    def refresh_rate(self, value):
        if type(value) != int:
            raise ValueError
        else:
            self._refresh_rate = min(max(1, value), 200)

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
        paths = filehandler.Paths.instance()
        d = filehandler.read_json(paths.config)
        self.from_dict(d)

    def to_disk(self):
        paths = filehandler.Paths.instance()
        d = self.as_dict()
        filehandler.write_json(paths.config, d)

    def from_dict(self, d):
        for field in fields(self):
            logging.info("{} <- {}".format(field.name, d[field.name]))
            setattr(self, field.name, d[field.name])

    def as_dict(self):
        return dict((field.name, getattr(self, field.name)) for field in fields(self))
