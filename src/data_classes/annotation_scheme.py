import logging
from collections import namedtuple

import src.data_classes.annotation as annotation


def scheme_is_valid(scheme):
    valid = True
    valid &= scheme is not None
    valid &= isinstance(scheme, list)
    valid &= len(scheme) > 0
    for x in scheme:
        valid &= isinstance(x, (list, tuple))
        valid &= len(x) == 2
        group_name, group_elements = x
        valid &= isinstance(group_name, str)
        valid &= isinstance(group_elements, list)
        valid &= len(group_elements) > 0
    return valid


class AnnotationScheme:
    def __init__(self, scheme: list):
        assert scheme_is_valid(scheme)
        self._scheme = scheme
        self._length = 0
        for _, gr in scheme:
            self._length += len(gr)

    def __len__(self):
        return self._length

    def __iter__(self):
        scheme_element = namedtuple(
            "scheme_element",
            ["group_name", "element_name", "row", "column"],
        )
        for row, (group_name, group_elements) in enumerate(self.scheme):
            for col, elem in enumerate(group_elements):
                yield scheme_element(group_name, elem, row, col)

    def get_empty_annotation(self):
        return annotation.Annotation(self)

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self):
        raise AttributeError("Cannot update the scheme")

    def __eq__(self, other):
        if isinstance(other, AnnotationScheme):
            if len(self) != len(other):
                return False
            for x, y in zip(self, other):
                if x != y:
                    return False
            return True
        else:
            return False
