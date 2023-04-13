import logging
import os
from typing import Tuple

import numpy as np
from torchvision.io import VideoReader

try:
    from .base import VideoReaderBase
except ImportError:
    from base import VideoReaderBase


class TorchVisionReader(VideoReaderBase):
    def __init__(self, path: os.PathLike, **kwargs):
        self.path = path
        self.video = VideoReader(path)

        print(f"{self.video.get_metadata() = }")

        self.pos = 0

        logging.info(f"Using torchvision for video {path}.")

    def get_frame(self, frame_idx: int) -> np.ndarray:
        if frame_idx != self.pos:
            timestamp = (frame_idx / self.get_fps()) - (1 / self.get_fps() / 2)
            print(f"Seeking to {timestamp = }")
            self.video.seek(timestamp)

        tmp = next(self.video)
        frame = tmp["data"].numpy().transpose(1, 2, 0)
        pts = tmp["pts"]
        self.pos = int(pts * self.get_fps())
        self.pos += 1

        print(f"[{frame.shape = }] {pts = } {self.pos = }")

        return frame

    def get_frame_count(self) -> int:
        return int(self.get_duration() * self.get_fps())

    def get_fps(self) -> float:
        return self.video.get_metadata()["video"]["fps"][0]

    def get_height(self) -> int:
        return 999

    def get_width(self) -> int:
        return 999

    def get_size(self) -> Tuple[int, int]:
        return self.get_width(), self.get_height()

    def get_duration(self) -> float:
        return self.video.get_metadata()["video"]["duration"][0]

    def get_fourcc(self) -> str:
        pass

    def get_codec(self) -> str:
        pass

    def get_path(self) -> os.PathLike:
        return self.path

    @staticmethod
    def is_supported(path: os.PathLike) -> bool:
        return True


try:
    from .base import register_video_reader  # noqa
except ImportError:
    from base import register_video_reader  # noqa

# register_video_reader(TorchVisionReader, -100)
logging.info("Registered TorchVisionReader.")
