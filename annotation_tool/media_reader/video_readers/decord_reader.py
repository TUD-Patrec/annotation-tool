import logging
import os
from typing import Tuple

try:
    import decord

    # use decord only for windows
    _use_decord = os.name == "nt"
except ImportError:
    logging.debug("Decord not available, falling back to OpenCV")
    decord = None
    _use_decord = False

import numpy as np

try:
    from .base import VideoReaderBase, register_video_reader
except ImportError:
    from base import VideoReaderBase, register_video_reader


class DecordReader(VideoReaderBase):
    """
    Video reader using decord.
    """

    def __init__(self, path: os.PathLike, **kwargs):
        """
        Initializes the video reader.

        Args:
            path (os.PathLike): The path to the video file.
        """
        self.path = path
        self.video = decord.VideoReader(path, ctx=decord.cpu(0))

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

    def get_height(self) -> int:
        """
        Returns the height of the video.

        Returns:
            int: The height of the video.
        """
        return self.video[0].shape[0]

    def get_width(self) -> int:
        """
        Returns the width of the video.

        Returns:
            int: The width of the video.
        """
        return self.video[0].shape[1]

    def get_size(self) -> Tuple[int, int]:
        return self.get_width(), self.get_height()

    def get_duration(self) -> float:
        """
        Returns the duration of the video in seconds.

        Returns:
            float: The duration of the video in seconds.
        """
        return self.get_frame_count() / self.get_fps()

    def get_codec(self) -> str:
        """
        Returns the codec of the video.

        Returns:
            str: The codec of the video.
        """
        raise NotImplementedError

    def get_fourcc(self) -> str:
        raise NotImplementedError

    def get_path(self) -> os.PathLike:
        return self.path

    @staticmethod
    def is_supported(path: str) -> bool:
        """
        Returns whether the video format is supported by the reader.

        Args:
            path (os.PathLike): The path to the video file.

        Returns:
            bool: True if the video format is supported, False otherwise.
        """
        # dont accept .avi
        if path.endswith(".avi"):
            return False
        try:
            decord_reader = decord.VideoReader(path)
            if len(decord_reader) <= 10:
                return False
            _ = [decord_reader[i] for i in range(10)]

            if decord_reader.get_avg_fps() < 1:
                return False

            return True
        except Exception:  # noqa
            return False


if _use_decord:
    register_video_reader(DecordReader, 1)

logging.info("Registered DecordReader.")
