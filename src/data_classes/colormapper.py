from dataclasses import dataclass, field
import logging

from .annotation import Annotation
from ..utility.decorators import Singleton
from distinctipy import distinctipy
import PyQt5.QtGui as qtg
import random


@Singleton
@dataclass()
class ColorMapper:
    _color_map: list = field(init=False)

    def __init__(self) -> None:
        random.seed(42)
        self._color_map = distinctipy.get_colors(50, n_attempts=250)

    def annotation_to_color(self, annotation: Annotation) -> qtg.QColor:
        assert annotation is not None
        assert isinstance(annotation, Annotation)

        x = 0
        for attribute in annotation:
            if attribute.row > 1:
                x += attribute.value * (2**attribute.array_index)

        x %= len(self._color_map)

        r, g, b = self._color_map[x]
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        color = qtg.QColor(r, g, b)
        color.setAlpha(127)

        return color
