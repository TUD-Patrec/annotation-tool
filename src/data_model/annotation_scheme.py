from collections import namedtuple
from dataclasses import dataclass, field
import logging


def scheme_is_valid(scheme):
    try:
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
    except Exception as e:
        logging.error(f"{e}")
        return False


def create_annotation_scheme(scheme: list):
    if scheme_is_valid(scheme):
        n = 0
        for _, gr in scheme:
            n += len(gr)
        return AnnotationScheme(scheme, str(scheme), n)
    else:
        raise ValueError(f"{scheme} is not valid")


@dataclass(frozen=True)
class AnnotationScheme:
    scheme: list = field(hash=False, compare=False)
    _scheme_str: str = field(hash=True, compare=True, repr=False)
    _n: int = field(hash=True, compare=True, repr=False)

    def __len__(self):
        return self._n

    def __iter__(self):
        scheme_element = namedtuple(
            "scheme_element",
            ["group_name", "element_name", "row", "column"],
        )
        for row, (group_name, group_elements) in enumerate(self.scheme):
            for col, elem in enumerate(group_elements):
                yield scheme_element(group_name, elem, row, col)
