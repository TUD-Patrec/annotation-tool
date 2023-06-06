import logging
import os
from pathlib import Path

try:
    import decord

    _use_decord = os.name == "nt"  # use decord only for windows
except ImportError:
    logging.debug("Decord not available, falling back to OpenCV")
    decord = None
    _use_decord = False

import numpy as np

from .base import VideoReaderBase, register_video_reader


class DecordReader(VideoReaderBase):
    """
    Video reader using decord.
    """

    def __init__(self, path: Path, **kwargs):
        """
        Initializes the video reader.

        Args:
            path (Path): The path to the video file.
        """
        self.path = path
        self.video = decord.VideoReader(path.as_posix(), ctx=decord.cpu(0))

        logging.info(f"Using decord for video {path}.")

    def get_frame(self, frame_idx: int) -> np.ndarray:
        """
        Returns the RGB-frame at the given index.

        Args:
            frame_idx (int): The index of the frame.

        Returns:
            np.ndarray: The frame as a numpy array. The shape is (height, width, channels).
                The channels are in RGB order.
        Raises:
            IndexError: If the frame index is out of bounds.
        """
        return self.video[frame_idx].asnumpy()

    def get_frame_count(self) -> int:
        """
        Returns the number of frames in the video.

        Returns:
            int: The number of frames.
        """
        return len(self.video)

    def get_fps(self) -> float:
        """
        Returns the frames per second of the video.

        Returns:
            float: The frames per second.
        """
        return self.video.get_avg_fps()

    def get_path(self) -> Path:
        return self.path

    @staticmethod
    def is_supported(path: Path) -> bool:
        """
        Returns whether the video format is supported by the reader.

        Args:
            path (Path): The path to the video file.

        Returns:
            bool: True if the video format is supported, False otherwise.
        """
        # dont accept .avi
        if path.suffix == ".avi":
            return False
        try:
            decord_reader = decord.VideoReader(path.as_posix())
            if len(decord_reader) <= 10:
                return False
            _ = [decord_reader[i] for i in range(10)]

            if decord_reader.get_avg_fps() < 1:
                return False

            return True
        except Exception:  # noqa
            return False


if _use_decord:
    register_video_reader(DecordReader, -1)  # too heavy on RAM

logging.info("Registered DecordReader.")
