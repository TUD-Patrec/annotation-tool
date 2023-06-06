from dataclasses import dataclass, field
import logging
from pathlib import Path
import time
from typing import List, Tuple

import numpy as np

from annotation_tool.file_cache import cached
from annotation_tool.media_reader import meta_data as get_meta_data
from annotation_tool.utility.decorators import accepts, returns
from annotation_tool.utility.filehandler import checksum, is_non_zero_file

from .dataset import Dataset
from .sample import Sample
from .single_annotation import empty_annotation


@cached
@dataclass
class Annotation:
    annotator_id: int
    _dataset: Dataset
    name: str
    _annotated_file: Path
    _checksum: str = field(init=False)
    _samples: list = field(init=False, default_factory=list)
    _creation_time: time.time = field(init=False, default_factory=time.time)
    _additional_media_paths: List[Tuple[Path, int]] = field(
        init=False, default_factory=list
    )
    _last_save: float = field(init=False, default_factory=time.time)

    def __post_init__(self):
        self._checksum = checksum(self.path)
        self.__init_samples__()

    def __init_samples__(self):
        n_frames = get_meta_data(self.path)["n_frames"]
        a = empty_annotation(self.dataset.scheme)
        s = Sample(0, n_frames - 1, a)
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
            self._last_save = time.time()

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
    def path(self) -> Path:
        return self._annotated_file

    @path.setter
    def path(self, path: Path):
        if not path.is_file():
            raise FileNotFoundError(path)
        if checksum(path) != self.checksum:
            raise ValueError("File has changed.")
        self._annotated_file = path

    @property
    def creation_time(self) -> time.struct_time:
        return time.localtime(self._creation_time)

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
        return int(n_annotations / n_frames * 100)

    @property
    def meta_data(self) -> dict:
        return {
            "annotator_id": self.annotator_id,
            "dataset": self.dataset.name,
            "file": self.path.as_posix(),
            "name": self.name,
            "creation_time": self.timestamp,
            "progress": self.progress,
        }

    @property
    def checksum(self) -> str:
        return self._checksum

    @property
    def last_save(self) -> float:
        return self._last_save

    def set_additional_media_paths(self, paths_with_offsets: List[Tuple[Path, int]]):
        additional_paths = []
        for p, o in paths_with_offsets:
            if not p.is_file():
                raise FileNotFoundError(p)
            additional_paths.append((p, o))
        self._additional_media_paths = additional_paths

    def get_additional_media_paths(self) -> List[Tuple[Path, int]]:
        return self._additional_media_paths


@returns(Annotation)
@accepts(int, Dataset, str, Path)
def create_annotation(
    annotator_id: int, dataset: Dataset, name: str, file_path: Path
) -> Annotation:
    """
    Creates a new GlobalState object.

    Args:
        annotator_id (int): The id of the annotator.
        dataset (Dataset): The dataset.
        name (str): The name of the annotation.
        file_path (Path): The path to the file to be annotated.

    Returns:
        Annotation: The new GlobalState object.
    Raises:
        ValueError If parameters are invalid.
    """
    if is_non_zero_file(file_path):
        return Annotation(annotator_id, dataset, name, file_path)
    else:
        raise ValueError(f"File {file_path} does not exist or is empty.")
