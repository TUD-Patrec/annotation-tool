# import torch
import enum
import os
from typing import Union, Tuple

import numpy as np
import PyQt5.QtCore as qtc
import torch

class NetworkType(enum.Enum):
    TCNN = 0


def run_network(data: Union[os.PathLike, np.ndarray, torch.Tensor], range: Tuple[int, int] = None, window_size: int = None, step_size: int = None, network_type: NetworkType = NetworkType.TCNN):
    # array_length = len(self.scheme)
    # return np.random.rand(array_length)
    pass


class NetworkController(qtc.QObject):


    def __init__(self, *args, **kwargs):
        super(NetworkController, self).__init__(*args, **kwargs)


    # Slots
