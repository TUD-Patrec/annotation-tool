import random

import PyQt5.QtGui as qtg
from distinctipy import distinctipy

from src.data_model.annotation import Annotation
from src.utility.decorators import Singleton


@Singleton
class ColorMapper:
    def __init__(self) -> None:
        random.seed(42)
        self._color_map = distinctipy.get_colors(50, n_attempts=250)

    def annotation_to_color(self, annotation: Annotation) -> qtg.QColor:
        assert annotation is not None
        assert isinstance(annotation, Annotation)

        x = 0
        for idx, attribute in enumerate(annotation):
            if attribute.row >= 1:
                break
            x += attribute.value * (2**idx)

        x %= len(self._color_map)

        r, g, b = self._color_map[x]
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        color = qtg.QColor(r, g, b)
        color.setAlpha(127)

        return color
