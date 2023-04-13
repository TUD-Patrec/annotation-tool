import dataclasses
import io
import logging
import math
from pathlib import Path
import threading
from typing import Optional

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
    def __init__(self, max_size_kb: int = 250000, compress=False):
        self._cache = []
        self._lock = threading.Lock()
        self._compress = compress

        self._max_size_bytes = max_size_kb * 1024
        self._current_size_bytes = 0

        logging.debug(f"Initialized {self}")

    def __len__(self):
        return len(self._cache)

    def __repr__(self):
        _len = len(self._cache)
        _size_kb = math.ceil(self._current_size_bytes / 1024)
        _max_size_kb = math.ceil(self._max_size_bytes / 1024)
        return f"MocapCache(len={_len}, size={_size_kb}KB, max_size={_max_size_kb}KB)"

    def __contains__(self, path: Path):
        _last_change = path.stat().st_mtime
        for obj in self._cache:
            if obj.path == path and obj.last_changed == _last_change:
                return True
        return False

    def __getitem__(self, path: Path):
        _last_change = path.stat().st_mtime
        for obj in reversed(self._cache):
            if obj.path == path and obj.last_changed == _last_change:
                return obj.data.copy()  # return a copy to avoid modifying the cache
        raise KeyError(f"Path {path} not found in cache.")

    def __setitem__(self, key, value):
        self.__put__(key, value)

    def __put__(self, path: Path, data: np.ndarray) -> None:
        assert isinstance(data, np.ndarray), "Data must be a numpy array."
        assert isinstance(path, Path), "Path must be a Path object."
        assert path.exists(), "Path must exist."

        with self._lock:
            compressed_data = CompressedArray(arr=data, compress=self._compress)
            new_obj = CachedMocapObject(compressed_data, path, path.stat().st_mtime)

            if new_obj.nbytes > 0.9 * self._max_size_bytes:
                logging.warning(
                    f"Object {path.name} is larger than the cache size. Skipping."
                )
                return

            self._current_size_bytes += compressed_data.nbytes
            self._evict()
            self._cache.append(new_obj)

        logging.debug(f"Added {path.name} to cache -> {self}")

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

    def get(self, path: Path, default=None) -> Optional[np.ndarray]:
        try:
            return self[path]
        except KeyError:
            return default

    def set_max_size(self, max_size_kb: int):
        with self._lock:
            self._max_size_bytes = max_size_kb * 1024
            self._evict()

    def set_compress(self, compress: bool):
        with self._lock:
            self._compress = compress


mocap_cache = MocapCache(compress=True)


def get_cache() -> MocapCache:
    return mocap_cache


def clear_cache():
    mocap_cache.clear()


def set_cache_max_size(max_size_kb: int):
    mocap_cache.set_max_size(max_size_kb)


def set_cache_compress(compress: bool):
    mocap_cache.set_compress(compress)
