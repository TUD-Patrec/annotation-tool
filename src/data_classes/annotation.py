from collections import namedtuple
from copy import deepcopy

import numpy as np
import logging

from typing import Union
from src.data_classes.annotation_scheme import AnnotationScheme
from src.utility.decorators import accepts, returns


def is_compatible(raw_annotation: Union[np.ndarray, dict], scheme: AnnotationScheme):
    if len(scheme) <= 0:
        return False
    if isinstance(raw_annotation, dict):
        for elem in scheme:
            val = raw_annotation.get(elem.row)(elem.column)
            if val is None:
                return False
            if not isinstance(val, int):
                return False
            if not val in [0, 1]:
                return False
        return True
    if isinstance(raw_annotation, np.ndarray):
        count = 0
        if len(scheme) != raw_annotation.shape[0]:
            return False
        if len(raw_annotation.shape) > 1:
            return False
        return np.all((raw_annotation == 0) | (raw_annotation == 1))

    return False


def empty_annotation(scheme: AnnotationScheme):
    return Annotation(None, scheme)


class Annotation:
    def __init__(self, scheme: AnnotationScheme, annotation: [np.ndarray, dict] = None):
        assert isinstance(scheme, AnnotationScheme)

        if annotation is None:
            annotation = np.zeros(len(scheme), dtype=np.int8)
        else:
            assert isinstance(annotation, (np.ndarray, dict))
            assert is_compatible(annotation, scheme)

        self._scheme = scheme
        self._annotation_dict = self._make_dict(annotation)
        self._annotation_vector = self._make_vector(annotation)

    def _make_dict(self, a):
        if isinstance(a, np.ndarray):
            d = {}
            row = -1
            for idx, scheme_element in enumerate(self.scheme):
                group_name = scheme_element.group_name
                if row != scheme_element.row:
                    row = scheme_element.row
                    d[group_name] = dict()

                group_element = scheme_element.element_name

                val = int(a[idx])
                assert 0 <= val <= 1
                d[group_name][group_element] = val
            return d
        if isinstance(a, dict):
            return a
        else:
            raise RuntimeError

    def _make_vector(self, a):
        if isinstance(a, np.ndarray):
            a = a.astype(dtype=np.int8)
            return a
        if isinstance(a, dict):
            ls = []
            for scheme_element in self.scheme:
                group_name, elem = (
                    scheme_element.group_name,
                    scheme_element.element_name,
                )
                val = a[group_name][elem]
                assert 0 <= val <= 1
                ls.append(val)
            return np.ndarray(ls, dtype=np.int8)
        else:
            raise RuntimeError

    def get_empty_copy(self):
        return Annotation(self.scheme)

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
        is_compatible(annotation, self.scheme)
        self._annotation_dict = self._make_dict(annotation)
        self._annotation_vector = self._make_vector(annotation)

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self, x):
        raise AttributeError("Cannot change the scheme!")

    def is_empty(self):
        return np.sum(self.annotation_vector) == 0

    def __len__(self):
        return self.annotation_vector.shape[0]

    def __eq__(self, other):
        if isinstance(other, Annotation):
            scheme_equal = self.scheme == other.scheme
            vec_equal = np.array_equal(self.annotation_vector, other.annotation_vector)
            return scheme_equal and vec_equal
        else:
            return False
    def __copy__(self):
        new_anno = Annotation(self.scheme, self.annotation_vector)
        assert self == new_anno and new_anno is not self
        return new_anno

    def __deepcopy__(self, memodict={}):
        new_anno = Annotation(deepcopy(self.scheme, memodict), deepcopy(self.annotation_vector, memodict))
        assert self == new_anno
        return new_anno

    def __iter__(self):
        annotation_element = namedtuple(
            "annotation_attribute",
            ["group_name", "element_name", "value", "row", "column"],
        )

        for scheme_element in self.scheme:
            group_name = scheme_element.group_name
            element_name = scheme_element.element_name
            row, col = scheme_element.row, scheme_element.column
            value = self.annotation_dict[group_name][element_name]

            yield annotation_element(group_name, element_name, value, row, col)
