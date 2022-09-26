import datetime
import logging
import os
import random
import string
import numpy as np
from dataclasses import dataclass, field
from typing import List
from .datasets import DatasetDescription
from .sample import Sample
from ..utility import filehandler
from src.data_classes.annotation import Annotation
from ..utility.decorators import accepts


@dataclass()
class GlobalState:
    _annotator_id: int
    _dataset: DatasetDescription
    _name: str
    _input_file: str
    _path: str = field(init=False)
    _footprint: str = field(init=False)
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

        _, self._frame_count, self._fps = filehandler.meta_data(
            self._input_file
        )

        empty_annotation = Annotation(self.dataset.scheme)
        self._samples.append(Sample(0, self._frame_count - 1, empty_annotation))


    @property
    def name(self):
        return self._name

    @name.setter
    @accepts(object, str)
    def name(self, value: str):
            self._name = value

    @property
    def path(self):
        return self._path

    @property
    def samples(self):
        return self._samples

    @samples.setter
    @accepts(object, list)
    def samples(self, value: List[Sample]):
        if len(value) == 0:
            raise ValueError("List must have at least 1 element.")
        else:
            last = -1
            for sample in value:
                if sample is None:
                    raise ValueError("Elements must not be None.")
                if not isinstance(sample, Sample):
                    raise ValueError("Elements must be from type Sample.")
                if sample.start_position != last + 1:
                    logging.error("Last = {} | sample = {}".format(last, sample))
                    raise ValueError("Gaps between Samples are not allowed!")
                last = sample.end_position

            N = value[-1].end_position + 1
            if N != self.n_frames:
                raise ValueError("Samples have wrong length")

            self._samples = value
            logging.info("Updating samples was succesfull!")

    @property
    def annotator_id(self):
        return self._annotator_id

    @annotator_id.setter
    @accepts(object, int)
    def annotator_id(self, value: int):
        self._annotator_id = value

    @property
    def input_file(self):
        return self._input_file

    @input_file.setter
    @accepts(object, (str, os.PathLike))
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
        return int(self.frames * 1000 / self.fps)

    @property
    def frames(self):
        return self.n_frames

    @property
    def n_frames(self):
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

