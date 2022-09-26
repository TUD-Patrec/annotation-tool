from dataclasses import dataclass, field

import PyQt5.QtGui as qtg

from .singletons import ColorMapper


@dataclass(order=True)
class Sample:
    _sort_index: int = field(init=False, repr=False)
    _start_pos: int = field(init=True)
    _end_pos: int = field(init=True)
    _annotation: dict = field(init=True, default_factory=dict)
    _default_color: qtg.QColor = field(init=False, default=None)
    _color: qtg.QColor = field(init=False, default=None)

    def __post_init__(self):
        self._default_color = qtg.QColor("#696969")
        self._default_color.setAlpha(127)
        self._sort_index = self._start_pos
        if not bool(self._annotation):
            self._color = None
        else:
            color_mapper = ColorMapper.instance()
            self._color = color_mapper.annotation_to_color(self._annotation)

    def __len__(self):
        return (self._end_pos - self._start_pos) + 1

    @property
    def start_position(self):
        return self._start_pos

    @start_position.setter
    def start_position(self, value):
        if type(value) != int:
            raise ValueError
        elif value < 0:
            raise ValueError
        else:
            self._start_pos = value

    @property
    def end_position(self):
        return self._end_pos

    @end_position.setter
    def end_position(self, value):
        if type(value) != int:
            raise ValueError
        elif value < 0:
            raise ValueError
        else:
            self._end_pos = value

    @property
    def annotation(self):
        return self._annotation

    @property
    def annotation_exists(self):
        return bool(self._annotation)  # False if {} else True

    @annotation.setter
    def annotation(self, value):
        if value is None:
            raise ValueError("None not allowed")
        elif type(value) != dict:
            raise ValueError
        else:
            self._annotation = value
            # empty annotation
            if not bool(value):
                self._color = None
            else:
                color_mapper = ColorMapper.instance()
                self._color = color_mapper.annotation_to_color(value)

    @property
    def color(self):
        if self._color is None:
            return self._default_color
        else:
            return self._color
