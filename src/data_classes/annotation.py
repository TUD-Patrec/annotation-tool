from collections import namedtuple

import numpy as np
from typing import Union

from src.utility.decorators import accepts, returns


def check_compatible(annotation: Union[np.ndarray, dict], scheme: list):
    if len(scheme) <= 0:
        return False
    if isinstance(annotation, dict):
        for gr_name, gr_elems in scheme:
            for elem in gr_elems:
                val = annotation.get(gr_name)(elem)
                if val is None:
                    return False
                if not isinstance(val, int):
                    return False
                if not (0 <= val <= 1):
                    return False
        return True
    if isinstance(annotation, np.ndarray):
        count = 0
        for gr_name, gr_elems in scheme:
            count += len(gr_elems)
        if count != annotation.shape[0]:
            return False
        if len(annotation.shape) > 1:
            return False
        for idx in range(annotation.shape[0]):
            if annotation[idx] < 0 or annotation[idx] > 1:
                return False
        return True

    return False


def empty_annotation(scheme: list):
    return Annotation(None, scheme)


class Annotation:
    def __init__(self, scheme: list, annotation: [np.ndarray, dict] = None):
        assert isinstance(scheme, list)

        if annotation is None:
            count = 0
            for gr_name, gr_elems in scheme:
                count += len(gr_elems)
            annotation = np.zeros(count, dtype=np.int8)
        else:
            check_compatible(annotation, scheme)
            assert isinstance(annotation, (np.ndarray, dict))

        self._scheme = scheme
        self._annotation_dict = self._make_dict(annotation)
        self._annotation_vector = self._make_vector(annotation)

    def _make_dict(self, a, scheme=None):
        if isinstance(a, np.ndarray):
            d = {}
            idx = 0
            for group_name, group_elements in self.scheme:
                d[group_name] = dict()
                for elem in group_elements:
                    val = a[idx]
                    assert 0 <= val <= 1
                    d[group_name][elem] = val
                    idx += 1
            return d
        if isinstance(a, dict):
            return a
        else:
            raise RuntimeError

    def _make_vector(self, a):
        if isinstance(a, np.ndarray):
            return a
        if isinstance(a, dict):
            ls = []
            for group_name, group_elements in self.scheme:
                for elem in group_elements:
                    val = a[group_name][elem]
                    assert 0 <= val <= 1
                    ls.append(val)
            return np.ndarray(ls, dtype=np.int8)
        else:
            raise RuntimeError

    def get_empty_copy(self):
        return Annotation(None, self.scheme)

    @property
    @returns(dict)
    def annotation_dict(self):
        return self._annotation_dict

    @property
    @returns(np.ndarray)
    def annotation_vector(self):
        return self._annotation_vector

    @property
    @returns((dict, np.ndarray))
    def annotation(self) -> (dict, np.ndarray):
        return self.annotation_dict, self.annotation_vector

    @annotation.setter
    def annotation(self, annotation: Union[np.ndarray, dict]):
        check_compatible(annotation, self.scheme)
        self._annotation_dict = self._make_dict(annotation)
        self._annotation_vector = self._make_vector(annotation)

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self, x):
        raise AttributeError('Cannot change the scheme!')

    @property
    def is_empty(self):
        return np.sum(self.annotation_vector) == 0

    def __len__(self):
        return self.annotation_vector.shape[0]

    def __iter__(self):
        annotation_element = namedtuple('annotation_attribute',
                                        ['group_name', 'element_name', 'value', 'row', 'column', 'array_index'])
        idx = 0
        for row, (group_name, group_elements) in enumerate(self.scheme):
            for col, elem in enumerate(group_elements):
                value = self.annotation_dict[group_name][elem]
                yield annotation_element(group_name, elem, value, row, col, idx)
                idx += 1
