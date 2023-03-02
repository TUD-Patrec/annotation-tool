from copy import deepcopy
from dataclasses import dataclass, field
import random
from typing import Tuple

from distinctipy import distinctipy

from annotation_tool.data_model.single_annotation import SingleAnnotation
from annotation_tool.utility.decorators import accepts_m, returns

random.seed(42)
__color_map__ = distinctipy.get_colors(50, n_attempts=250)
__default_color__ = 105, 105, 105


def __annotation_to_color__(annotation: SingleAnnotation) -> Tuple[int, int, int, int]:
    """
    Converts an annotation to a color.

     Args:
        annotation: The annotation to convert.

    Returns:
        The color of the annotation as a (r, g, b) tuple.
    """
    if annotation is None:
        raise ValueError("Annotation must not be None.")
    if annotation.is_empty():
        return __default_color__
    x = 0
    for idx, attribute in enumerate(annotation):
        if attribute.row >= 1:
            break
        x += attribute.value * (2**idx)

    x %= len(__color_map__)

    r, g, b = __color_map__[x]
    r, g, b = int(r * 255), int(g * 255), int(b * 255)

    return r, g, b


@dataclass(order=True, unsafe_hash=True)
class Sample:
    _sort_index: int = field(init=False, repr=False, hash=False, compare=False)
    _start_pos: int = field(init=True, hash=True, compare=True)
    _end_pos: int = field(init=True, hash=True, compare=True)
    _annotation: SingleAnnotation = field(init=True, hash=False, compare=False)

    def __post_init__(self):
        assert isinstance(self._start_pos, int)
        assert isinstance(self._end_pos, int)
        assert isinstance(self._annotation, SingleAnnotation)
        assert self._start_pos <= self._end_pos
        assert self._start_pos >= 0

        self._sort_index = self._start_pos

    def __len__(self):
        return (self._end_pos - self._start_pos) + 1

    @property
    @returns(int)
    def start_position(self):
        return self._start_pos

    @start_position.setter
    @accepts_m(int)
    def start_position(self, value):
        if value < 0:
            raise ValueError
        else:
            self._start_pos = value

    @property
    @returns(int)
    def end_position(self):
        return self._end_pos

    @end_position.setter
    @accepts_m(int)
    def end_position(self, value):
        if value < 0:
            raise ValueError
        else:
            self._end_pos = value

    @property
    @returns(SingleAnnotation)
    def annotation(self):
        return self._annotation

    @annotation.setter
    @accepts_m(SingleAnnotation)
    def annotation(self, value):
        if value is None:
            raise ValueError("None not allowed")
        # check compatibility
        if self.annotation.scheme != value.scheme:
            raise ValueError("Incompatible schemes")
        self._annotation = value

    @property
    def color(self):
        return __annotation_to_color__(self._annotation)

    def __copy__(self):
        return Sample(self._start_pos, self._end_pos, self._annotation)

    def __deepcopy__(self, memo):
        return Sample(self._start_pos, self._end_pos, deepcopy(self._annotation))


def create_sample(start_pos: int, end_pos: int, annotation: SingleAnnotation) -> Sample:
    """
    Creates a new sample.

    Args:
        start_pos: The start position of the sample.
        end_pos: The end position of the sample.
        annotation: The annotation of the sample.

    Returns:
        The created sample.

    Raises:
        ValueError: If the parameters are invalid.
    """
    try:
        return Sample(start_pos, end_pos, annotation)
    except AssertionError:
        raise ValueError("Invalid sample.")
