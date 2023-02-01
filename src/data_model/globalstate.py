from dataclasses import dataclass, field
import logging
import math
import os
import time
from typing import List

import numpy as np

from src.file_cache import cached
from src.utility.decorators import accepts
from src.utility.filehandler import footprint_of_file

from .annotation import empty_annotation
from .dataset import Dataset
from .sample import Sample


@cached
@dataclass
class GlobalState:
    annotator_id: int
    _dataset: Dataset
    name: str
    _path: os.PathLike
    _footprint: str = field(init=False)
    _samples: list = field(init=False, default_factory=list)
    _timestamp: time.struct_time = field(init=False, default_factory=time.localtime)

    def __post_init__(self):
        # finish initialization
        from src.media_reader import MediaReader, media_reader
        from src.utility.filehandler import footprint_of_file

        media: MediaReader = media_reader(self.path)
        self._footprint = footprint_of_file(self.path)

        a = empty_annotation(self.dataset.scheme)
        s = Sample(0, len(media) - 1, a)
        self.samples.append(s)

    @property
    def samples(self) -> List[Sample]:
        return self._samples

    @samples.setter
    @accepts(object, list)
    def samples(self, list_of_samples: List[Sample]):
        if len(list_of_samples) == 0:
            raise ValueError("List must have at least 1 element.")
        else:
            last = -1
            for sample in list_of_samples:
                if sample is None:
                    raise ValueError("Elements must not be None.")
                if not isinstance(sample, Sample):
                    raise ValueError("Elements must be from type Sample.")
                if sample.start_position != last + 1:
                    logging.error("Last = {} | sample = {}".format(last, sample))
                    raise ValueError("Gaps between Samples are not allowed!")
                last = sample.end_position

            self._samples = list_of_samples
            logging.info("Updating samples was succesfull!")

    def to_numpy(self) -> np.ndarray:
        """
        Converts the samples to a numpy array.

        Returns:
            np.ndarray: The samples as a numpy array.
        """
        x = []
        for sample in self.samples:
            lower = sample.start_position
            upper = sample.end_position
            annotation_vector = sample.annotation.annotation_vector

            for _ in range(lower, upper + 1):
                x.append(annotation_vector)
        x = np.array(x, int)
        return x

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    @property
    def path(self) -> os.PathLike:
        return self._path

    @path.setter
    def path(self, path: os.PathLike):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        if footprint_of_file(path) != self._footprint:
            raise ValueError("File has changed.")
        self._path = path

    @property
    def creation_time(self) -> time.struct_time:
        return self._timestamp

    @property
    def timestamp(self) -> str:
        return time.strftime("%Y-%m-%d_%H-%M-%S", self.creation_time)

    @property
    def progress(self) -> int:
        """
        Returns the annotation progress in percent.
        (Rounded up to the next integer)
        """
        n_frames = self.samples[-1].end_position + 1
        n_annotations = sum(
            [
                s.end_position - s.start_position + 1
                for s in self.samples
                if not s.annotation.is_empty()
            ]
        )
        return math.ceil(n_annotations / n_frames * 100)

    @property
    def meta_data(self) -> dict:
        return {
            "annotator_id": self.annotator_id,
            "dataset": self.dataset.name,
            "file": self.path,
            "name": self.name,
            "creation_time": self.timestamp,
            "progress": self.progress,
        }

    @property
    def footprint(self) -> str:
        return self._footprint
