from dataclasses import dataclass, field
import logging
from typing import List

import numpy as np

from src.data_model.annotation import empty_annotation

from ..media.media_base import MediaBase
from ..utility.decorators import accepts
from ..utility.file_cache import Cachable
from .dataset import Dataset
from .sample import Sample


@dataclass
class GlobalState(Cachable):
    annotator_id: int
    dataset: Dataset
    name: str
    media: MediaBase
    _samples: list = field(init=False, default_factory=list)

    def __post_init__(self):
        super().__init__()
        a = empty_annotation(self.dataset.scheme)
        s = Sample(0, self.media.n_frames - 1, a)
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
