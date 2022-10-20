from dataclasses import dataclass, field

from src.dataclasses import Annotation, Sample


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
        return Sample(self.start, self.end, self.annotation)


def create_sub_intervals(intervals, stepsize, interval_size):
    res = []
    for intrvl in intervals:
        res += partition_interval(intrvl, stepsize, interval_size)
    return res


def partition_interval(interval, stepsize, interval_size):
    # ascending
    asc_partition = []
    lo, hi = interval

    while lo + interval_size - 1 <= hi:
        upper = lo + interval_size - 1
        asc_partition.append((lo, upper))
        lo = lo + stepsize

    # descending
    desc_partition = []
    lo, hi = interval

    while lo + interval_size - 1 <= hi:
        lower = hi - interval_size + 1
        desc_partition.append((lower, hi))
        hi = hi - stepsize

    # join both lists
    combined_partition = []
    for (a_lo, a_hi), (d_lo, d_hi) in zip(asc_partition, desc_partition):
        if a_lo == d_lo:
            combined_partition.append((a_lo, a_hi))
        elif a_lo > d_lo:
            break
        else:
            combined_partition.append((a_lo, a_hi))
            combined_partition.append((d_lo, d_hi))

    combined_partition.sort()

    return combined_partition


def create_smallest_description(intervals):
    intervals.sort()
    res = []
    for tpl in intervals:
        lo = min(tpl)
        hi = max(tpl)
        if len(res) > 0:
            prev_lo, prev_hi = res.pop()
            # merge possible
            if lo <= prev_hi + 1:
                res.append((prev_lo, hi))
            else:
                res.append((prev_lo, prev_hi))
                res.append((lo, hi))
        else:
            res.append((lo, hi))
    return res


def generate_intervals(ranges, stepsize, interval_size):
    if len(ranges) == 0:
        return []

    # generate smallest description of ranges -> merge adjacent tuples
    ranges = create_smallest_description(ranges)
    print(f"{ranges = }")

    # create sub_intervals inside each range
    sub_intervals = create_sub_intervals(ranges, stepsize, interval_size)
    print(f"{sub_intervals = }")

    return sub_intervals
