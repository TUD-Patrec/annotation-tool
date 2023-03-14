import copy
from dataclasses import dataclass, field
import json
import logging
import math
import os
import time
from typing import List

import numpy as np

from annotation_tool.file_cache import cached
from annotation_tool.utility.decorators import accepts
from annotation_tool.utility.filehandler import footprint_of_file

from .dataset import Dataset
from .sample import Sample
from .single_annotation import empty_annotation


@cached
@dataclass
class Annotation:
    annotator_id: int
    _dataset: Dataset
    name: str
    _media_path: os.PathLike
    _footprint: str = field(init=False)
    _samples: list = field(init=False, default_factory=list)
    _timestamp: time.struct_time = field(init=False, default_factory=time.localtime)
    _additional_media_paths: List[os.PathLike] = field(init=False, default_factory=list)

    def __post_init__(self):
        # finish initialization
        from annotation_tool.utility.filehandler import footprint_of_file

        self.__init_valid__()
        self._footprint = footprint_of_file(self.path)
        self.__init_samples__()

    def __init_valid__(self):
        assert self.dataset is not None, "Dataset must not be None."
        assert isinstance(self.dataset, Dataset), "Dataset must be of type Dataset."
        assert self.name is not None, "Name must not be None."
        assert isinstance(self.name, str), "Name must be of type str."
        assert len(self.name) > 0, "Name must not be empty."
        assert self.annotator_id is not None, "Annotator ID must not be None."
        assert isinstance(self.annotator_id, int), "Annotator ID must be of type int."
        assert (
            self.annotator_id >= 0
        ), "Annotator ID must be greater than or equal to 0."
        assert self.path is not None, "Path must not be None."
        assert isinstance(
            self.path, (str, os.PathLike)
        ), "Path must be of type os.PathLike."
        assert os.path.isfile(self.path), "Path must be a file."
        assert os.path.getsize(self.path) > 0, "Path must not be empty."

    def __init_samples__(self):
        from annotation_tool.media_reader import MediaReader, media_reader

        media: MediaReader = media_reader(self.path)

        a = empty_annotation(self.dataset.scheme)
        s = Sample(0, len(media) - 1, a)
        self._samples.append(s)

    @property
    def samples(self) -> List[Sample]:
        # assert len(self._samples) > 0, "Samples must not be empty."
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

            for _ in range(upper - lower + 1):
                x.append(annotation_vector)
        x = np.array(x, int)
        return x

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    @property
    def path(self) -> os.PathLike:
        return self._media_path

    @path.setter
    def path(self, path: os.PathLike):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        if footprint_of_file(path) != self.footprint:
            raise ValueError("File has changed.")
        self._media_path = path

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

    def set_additional_media_paths(self, paths: List[os.PathLike]):
        additional_paths = []
        for x in paths:
            if not os.path.isfile(x):
                raise FileNotFoundError(x)
            additional_paths.append(x)
        self._additional_media_paths = additional_paths

    def get_additional_media_paths(self) -> List[os.PathLike]:
        return self._additional_media_paths

    # TODO: update copy functions (additional media paths)
    def __copy__(self):
        return Annotation(
            self.annotator_id,
            self.dataset,
            self.name,
            self.path,
        )

    def __deepcopy__(self, memodict={}):
        return Annotation(
            self.annotator_id,
            copy.deepcopy(self.dataset),
            self.name,
            self.path,
        )

    def to_dict(self) -> dict:
        _annotations = []
        for sample in self.samples:
            _tmp = {
                "start": sample.start_position,
                "end": sample.end_position,
                "annotation": sample.annotation.annotation_dict,
            }
            _annotations.append(_tmp)

        _dataset = self.dataset.to_dict()

        _additional_media_paths = self._additional_media_paths

        _d = {
            "annotator_id": self.annotator_id,
            "dataset": _dataset,
            "annotations": _annotations,
            "name": self.name,
            "path": self.path,
            "footprint": self.footprint,
            "timestamp": self.timestamp,
            "additional_media_paths": _additional_media_paths,
        }
        return _d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4, sort_keys=True, ensure_ascii=False)


def create_global_state(
    annotator_id: int, dataset: Dataset, name: str, path: os.PathLike
) -> Annotation:
    """
    Creates a new GlobalState object.

    Args:
        annotator_id (int): The id of the annotator.
        dataset (Dataset): The dataset.
        name (str): The name of the annotation.
        path (os.PathLike): The path to the media file.

    Returns:
        Annotation: The new GlobalState object.
    Raises:
        ValueError If parameters are invalid.
    """
    try:
        return Annotation(annotator_id, dataset, name, path)
    except AssertionError as e:
        raise ValueError(e)
