from dataclasses import dataclass, field, fields
import logging

from src.utility import filehandler
from src.utility.decorators import Singleton, accepts_m


@Singleton
@dataclass()
class Settings:
    _annotator_id: int = field(init=False, default=0)
    _debugging_mode: bool = field(init=False, default=False)
    _window_x: int = field(init=False, default=1200)
    _window_y: int = field(init=False, default=700)
    _dark_mode: bool = field(init=False, default=False)
    _font: int = field(init=False, default=10)
    _refresh_rate: int = field(init=False, default=200)
    _show_millisecs: bool = field(init=False, default=False)
    _retrieval_segment_size: int = field(init=False, default=200)
    _retrieval_segment_overlap: float = field(init=False, default=0)
    _small_skip: int = field(init=False, default=1)
    _big_skip: int = field(init=False, default=100)

    def __post_init__(self):
        paths = filehandler.Paths.instance()
        if not filehandler.is_non_zero_file(paths.config):
            self.to_disk()
        else:
            self.from_disk()

    @property
    def retrieval_segment_size(self):
        return self._retrieval_segment_size

    @retrieval_segment_size.setter
    @accepts_m(int)
    def retrieval_segment_size(self, x):
        if x > 0:
            self._retrieval_segment_size = x
        else:
            raise ValueError(f"{x = } needs to be bigger than 0 ")

    @property
    def retrieval_segment_overlap(self):
        return self._retrieval_segment_overlap

    @retrieval_segment_overlap.setter
    @accepts_m(float)
    def retrieval_segment_overlap(self, x):
        if 0 <= x < 1:
            self._retrieval_segment_overlap = x
        else:
            raise ValueError(f"{x = } needs to be in [0, 1)")

    @property
    def annotator_id(self):
        return self._annotator_id

    @annotator_id.setter
    @accepts_m(int)
    def annotator_id(self, value):
        self._annotator_id = value

    @property
    def debugging_mode(self):
        return self._debugging_mode

    @debugging_mode.setter
    @accepts_m(bool)
    def debugging_mode(self, value):
        self._debugging_mode = value

    @property
    def window_x(self):
        return self._window_x

    @window_x.setter
    @accepts_m(int)
    def window_x(self, value):
        self._window_x = value

    @property
    def window_y(self):
        return self._window_y

    @window_y.setter
    @accepts_m(int)
    def window_y(self, value):
        self._window_y = value

    @property
    def darkmode(self):
        return self._dark_mode

    @darkmode.setter
    @accepts_m(bool)
    def darkmode(self, value):
        self._dark_mode = value

    @property
    def font(self):
        return self._font

    @font.setter
    @accepts_m(int)
    def font(self, value):
        self._font = min(max(6, value), 30)

    @property
    def refresh_rate(self):
        return self._refresh_rate

    @refresh_rate.setter
    @accepts_m(int)
    def refresh_rate(self, value):
        self._refresh_rate = min(max(1, value), 500)

    @property
    def show_millisecs(self):
        return self._show_millisecs

    @show_millisecs.setter
    @accepts_m(bool)
    def show_millisecs(self, value):
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
        for fld in fields(self):
            setattr(self, fld.name, fld.default)

    def from_disk(self):
        paths = filehandler.Paths.instance()
        d = filehandler.read_json(paths.config)
        self.from_dict(d)

    def to_disk(self):
        paths = filehandler.Paths.instance()
        d = self.as_dict()
        filehandler.write_json(paths.config, d)

    def from_dict(self, d):
        for fld in fields(self):
            logging.info("{} <- {}".format(fld.name, d[fld.name]))
            setattr(self, fld.name, d[fld.name])

    def as_dict(self):
        return dict((field.name, getattr(self, field.name)) for field in fields(self))
