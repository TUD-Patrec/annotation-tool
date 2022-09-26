from dataclasses import dataclass, field
import datetime
import logging
import os
import random
import re
import string
from typing import List

import numpy as np

from ..utility import filehandler
from .datasets import DatasetDescription
from .sample import Sample


@dataclass()
class Annotation:
    _annotator_id: int
    _dataset: DatasetDescription
    _name: str
    _input_file: str
    _try_media_player: bool = field(init=True, default=True)
    _path: str = field(init=False)
    _footprint: str = field(init=False)
    _last_edited: datetime.datetime = field(init=False, default=datetime.datetime.now())
    _samples: list = field(init=False, default_factory=list)

    def __post_init__(self):
        if not filehandler.is_non_zero_file(self._input_file):
            raise FileNotFoundError(self._input_file)

        paths = filehandler.Paths.instance()

        random_str = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        file_name = self._name + "_" + random_str + "_.pkl"

        path = os.path.join(paths.annotations, file_name)
        while os.path.isfile(path):
            random_str = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=5)
            )
            file_name = self._name + "_" + random_str + "_.pkl"
            path = os.path.join(paths.annotations, file_name)

        self._path = path
        self._footprint = filehandler.footprint_of_file(self._input_file)

        self._duration, self._frame_count, self._fps = filehandler.meta_data(
            self._input_file
        )

        self._samples.append(Sample(0, self._frame_count - 1))

    def __len__(self):
        return self._samples[-1].end_position + 1

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if type(value) != str:
            raise ValueError("Must be a string.")
        else:
            self._name = value

    @property
    def path(self):
        return self._path

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def samples(self, value: List[Sample]):
        if type(value) != list:
            raise ValueError("Must be a list.")
        elif len(value) == 0:
            raise ValueError("List must have at least 1 element.")
        else:
            last = -1
            for sample in value:
                if sample is None:
                    raise ValueError("Elements must not be None.")
                if type(sample) != Sample:
                    raise ValueError("Elements must be from type Sample.")
                if sample.start_position != last + 1:
                    print("Last = {} | sample = {}".format(last, sample))
                    raise ValueError("Gaps between Samples are not allowed!")
                last = sample.end_position

            N = value[-1].end_position + 1
            if N != len(self):
                raise ValueError("Samples have wrong length")

            self._samples = value
            self.__update_last_edit__()
            logging.info("Updating samples was succesfull!")

    @property
    def annotator_id(self):
        return self._annotator_id

    @annotator_id.setter
    def annotator_id(self, value: int):
        if type(value) != int:
            raise ValueError("Must be an Integer")
        else:
            self._annotator_id = value

    @property
    def input_file(self):
        return self._input_file

    @input_file.setter
    def input_file(self, value: os.PathLike):
        if not filehandler.is_non_zero_file(value):
            raise FileNotFoundError(value)
        elif filehandler.footprint_of_file(value) != self._footprint:
            raise FileNotFoundError("footprint of {} does not match.".format(value))
        else:
            self._input_file = value

    @property
    def dataset(self):
        return self._dataset

    @property
    def footprint(self):
        return self._footprint

    @property
    def frame_based_annotation(self):
        return not self._try_media_player

    @property
    def fps(self):
        return self._fps

    @property
    def duration(self):
        return self._duration

    @property
    def frames(self):
        # only for compatibility
        # remove later
        if not hasattr(self, "_frame_count"):
            self._duration, self._frame_count, self._fps = filehandler.meta_data(
                self._input_file
            )
        return self._frame_count

    def to_numpy(self):
        x = []
        for sample in self.samples:
            lower = sample.start_position
            upper = sample.end_position

            vec = []
            for group_name, group_elements in self.dataset.scheme:
                for elem in group_elements:
                    if bool(sample.annotation):
                        val = sample.annotation[group_name][elem]
                    else:
                        val = 0
                    vec.append(val)
            annotation_vector = np.array(vec, dtype=np.uint8)

            for _ in range(lower, upper + 1):
                x.append(annotation_vector)
        x = np.array(x, int)
        return x

    def to_disk(self):
        filehandler.write_pickle(self._path, self)

    @staticmethod
    def from_disk(path):
        if filehandler.is_non_zero_file(path):
            try:
                annotation = filehandler.read_pickle(path)
                annotation._path = path
                return annotation
            except:
                raise FileNotFoundError("Could not open {}".format(path))

    def __update_last_edit__(self):
        self.last_edited = datetime.datetime.now()
