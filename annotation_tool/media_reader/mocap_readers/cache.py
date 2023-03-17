import dataclasses
import io
import logging
import math
from pathlib import Path
import threading
from typing import Optional, Union

import numpy as np


class CompressedArray:
    def __init__(self, arr: np.ndarray, compress=False):
        if compress:
            compressed_data = io.BytesIO()
            np.savez_compressed(compressed_data, arr)
            print(
                f"Compressed {arr.nbytes / 1024} KB to {compressed_data.getbuffer().nbytes / 1024} KB"
            )
            self._arr = compressed_data
        else:
            self._arr = arr

        self._compressed = compress

    @property
    def data(self):
        if self._compressed:
            self._arr.seek(0)
            return np.load(self._arr)["arr_0"]
        else:
            return self._arr

    @property
    def nbytes(self):
        if self._compressed:
            return self._arr.getbuffer().nbytes
        else:
            return self._arr.nbytes


@dataclasses.dataclass(frozen=True, eq=True)
class CachedMocapObject:
    compressed_data: CompressedArray = dataclasses.field(hash=False, compare=False)
    path: Path = dataclasses.field(hash=True, compare=True)
    last_changed: float = dataclasses.field(hash=True, compare=True)

    @property
    def data(self):
        return self.compressed_data.data

    @property
    def nbytes(self):
        return self.compressed_data.nbytes


class MocapCache(object):
    def __init__(self, max_size_kb: int = 500000):
        self._cache = []
        self._lock = threading.Lock()

        self._max_size_bytes = max_size_kb * 1024
        self._current_size_bytes = 0

        print(f"{self = }")

    def __len__(self):
        return len(self._cache)

    def __repr__(self):
        _len = len(self._cache)
        _size_kb = math.ceil(self._current_size_bytes / 1024)
        _max_size_kb = math.ceil(self._max_size_bytes / 1024)
        return f"MocapCache(len={_len}, size={_size_kb}KB, max_size={_max_size_kb}KB)"

    def __contains__(self, path: Union[Path, str]):
        return self.get(path) is not None

    def __getitem__(self, path: Union[Path, str]):
        x = self.get(path)
        if x is None:
            raise KeyError(f"Path {path} not found in cache.")
        return x

    def __setitem__(self, key, value):
        self.put(key, value)

    def _evict(self):
        untouched = True
        while self._current_size_bytes > self._max_size_bytes:
            self._current_size_bytes -= self._cache.pop(0).data.nbytes
            untouched = False
        if not untouched:
            logging.debug(f"Evicted cache -> {self}")

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._current_size_bytes = 0
        logging.debug(f"Cleared cache -> {self}")

    def get(self, path: Union[Path, str], default=None) -> Optional[np.ndarray]:
        if isinstance(path, str):
            path = Path(path)
        for obj in self._cache:
            if obj.path == path and obj.last_changed == path.stat().st_mtime:
                return obj.data
        return default

    def put(self, path: Union[Path, str], data: np.ndarray) -> None:
        assert isinstance(data, np.ndarray), "Data must be a numpy array."
        assert isinstance(path, (Path, str)), "Path must be a path-like object."
        if isinstance(path, str):
            path = Path(path)
        with self._lock:
            compressed_data = CompressedArray(data)
            new_obj = CachedMocapObject(compressed_data, path, path.stat().st_mtime)
            if new_obj in self._cache:
                return
            self._cache.append(new_obj)
            self._current_size_bytes += compressed_data.nbytes
            self._evict()
        logging.debug(f"Added {path.name} to cache -> {self}")

    def set_max_size(self, max_size_kb: int):
        with self._lock:
            self._max_size_bytes = max_size_kb * 1024
            self._evict()


mocap_cache = MocapCache()
