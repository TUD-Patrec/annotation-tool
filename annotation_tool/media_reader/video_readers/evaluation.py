import dataclasses
import os
from time import perf_counter

try:
    from .decord_reader import DecordReader
    from .opencv_reader import OpenCvReader
except ImportError:
    from opencv_reader import OpenCvReader
    from decord_reader import DecordReader

import numpy as np

try:
    video_folder = r"C:\Users\Raphael\Desktop\example_videos"
    for p in os.walk(video_folder):
        in_files = [os.path.join(p[0], f) for f in p[2]]
except:  # noqa: E722
    in_files = []


print(in_files)


readers = [OpenCvReader, DecordReader]

results = []

random_seed = 42


@dataclasses.dataclass
class Result:
    reader: str
    file_path: str
    detected_frame_count: int
    detected_fps: float
    detected_duration: float
    video_size: tuple
    access_test_type: str
    total_time: float
    number_repetitions: int
    frames_per_second: float = dataclasses.field(init=False)

    def __post_init__(self):
        self.frames_per_second = self.number_repetitions / self.total_time


def random_access_test(N=100):
    print("** Random access test **")

    for vr in readers:
        for in_file in in_files:
            print("Testing", vr.__name__, in_file + " ...")

            active_vr = vr(in_file)

            n_frames = active_vr.get_frame_count()
            fps = active_vr.get_fps()
            duration = active_vr.get_duration()
            size = active_vr.get_size()

            n_trials = min(N, n_frames)

            np.random.seed(random_seed)
            random_indices = np.random.randint(0, n_frames, n_trials, dtype=int)

            start = perf_counter()
            for i in tqdm.tqdm(random_indices):
                active_vr.get_frame(i)
            end = perf_counter()

            result = Result(
                reader=vr.__name__,
                file_path=in_file,
                detected_frame_count=n_frames,
                detected_fps=fps,
                detected_duration=duration,
                video_size=size,
                access_test_type="random",
                total_time=end - start,
                number_repetitions=n_trials,
            )
            results.append(result)
            print()

    print("** Random access test finished **\n")


def sequential_access_test(N=100):
    print("** Sequential access test **")

    for vr in readers:
        for in_file in in_files:
            print("Testing", vr.__name__, in_file + " ...")

            active_vr = vr(in_file)

            n_frames = active_vr.get_frame_count()
            fps = active_vr.get_fps()
            duration = active_vr.get_duration()
            size = active_vr.get_size()

            start = perf_counter()

            n_trials = min(N, n_frames)

            for i in tqdm.tqdm(range(n_trials)):
                active_vr.get_frame(i)
            end = perf_counter()

            result = Result(
                reader=vr.__name__,
                file_path=in_file,
                detected_frame_count=n_frames,
                detected_fps=fps,
                detected_duration=duration,
                video_size=size,
                access_test_type="sequential",
                total_time=end - start,
                number_repetitions=n_trials,
            )
            results.append(result)
            print()

    print("Random access test finished")


if __name__ == "__main__":
    try:
        import tqdm
    except ImportError:
        print("tqdm not installed. Please install tqdm to run this script.")
        exit()
    sequential_access_test(1000)
    random_access_test(100)

    results.sort(key=lambda x: (x.reader, x.file_path))

    for res in results:
        print(res)

    # save results to csv
    import csv

    out_path = r"C:\Users\Raphael\Desktop\results.csv"
    with open(out_path, "w", newline="") as csvfile:
        fieldnames = [
            "reader",
            "file_path",
            "detected_frame_count",
            "detected_fps",
            "detected_duration",
            "video_size",
            "access_test_type",
            "total_time",
            "number_repetitions",
            "frames_per_second",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(dataclasses.asdict(res))
