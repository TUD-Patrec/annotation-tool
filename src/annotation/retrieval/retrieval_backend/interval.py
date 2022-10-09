import logging
import math
import time
from copy import deepcopy
from dataclasses import dataclass, field

from src.data_classes import Annotation, Sample
from src.utility.decorators import accepts


@dataclass(unsafe_hash=True, order=True)
class Interval:
    _sort_index: int = field(init=False, repr=False, compare=False)
    start: int = field(hash=True, compare=True)
    end: int = field(hash=True, compare=True)
    annotation: Annotation = field(hash=True, compare=False)
    similarity: float = field(hash=True, compare=False)

    def __post_init__(self):
        self._sort_index = self.start

    def as_sample(self):
        anno = deepcopy(self.annotation)
        sample = Sample(self.start, self.end, anno)


@accepts(list)
def generate_intervals(ranges, stepsize, interval_size):
    start_time = time.perf_counter()

    if len(ranges) == 0:
        return

    ranges.sort()

    # generate smallest description of ranges -> merge adjacent tuples
    ls = []

    for lo, hi in ranges:
        if len(ls) > 0:
            prev_lo, prev_hi = ls.pop()
            # merge possible
            if lo <= prev_hi + 1:
                ls.append((prev_lo, hi))
            else:
                ls.append((prev_lo, prev_hi))
                ls.append((lo, hi))
        else:
            ls.append((lo, hi))

    boundaries = []
    for sample in self.samples:
        # sample already annotated
        if not sample.annotation.is_empty():
            continue

        # only grab samples that are not annotated yet
        l, r = sample.start_position, sample.end_position
        boundaries.append([l, r])

    # merge adjacent intervals
    reduced_boundaries = []
    idx = 0
    while idx < len(boundaries):
        l, r = boundaries[idx]

        nxt_idx = idx + 1
        while nxt_idx < len(boundaries) and boundaries[nxt_idx][0] == r + 1:
            _, r = boundaries[nxt_idx]
            nxt_idx += 1
        reduced_boundaries.append([l, r])
        idx = nxt_idx

    intervals = []
    for l, r in reduced_boundaries:
        tmp = get_intervals_in_range(l, r)
        intervals.extend(tmp)

    end_time = time.perf_counter()
    logging.debug(f"GENERATING INTERVALS TOOK {end_time - start_time}ms")
    return intervals


def get_intervals_in_range(lo, hi):
    if hi <= lo:
        return []

    intervals = []
    last_intervals = []
    start = lo
    stepsize = self.stepsize()

    while start <= hi:
        end = min(start + self._interval_size - 1, hi)

        if end == hi:
            # 1) if intervals has elements -> extend the last interval to end at the new end-position
            if last_intervals:
                logging.debug("Extending last interval")
                for i in last_intervals:
                    i.end = end

            # 2) if intervals is empty -> extend the interval left and right to the needed size for the network
            else:
                logging.debug("Extending interval left and right")
                start_adjusted = max(0, start - self._interval_size)
                end_adjusted = start_adjusted + self._interval_size - 1

                # find best sourrounding interval
                while (
                    end_adjusted < self.n_frames - 1
                    and start_adjusted < start - self._interval_size // 2
                ):
                    start_adjusted += 1
                    end_adjusted += 1

                # make sure that the adjusted interval is within the video/Mocap
                if end_adjusted < self.n_frames:
                    preds = self.get_predictions(start_adjusted, end_adjusted)
                    for i in preds:
                        intervals.append(i)
                        i.start = start
                        i.end = end
                else:
                    logging.warning(
                        f"Was not able to create interval that is small enough to fit inside the video/mocap -> n_frames is smaller than interval_size!"
                    )
        else:
            last_intervals = []
            for i in self.get_predictions(start, end):
                last_intervals.append(i)
                intervals.append(i)

        start = start + stepsize

    return intervals
