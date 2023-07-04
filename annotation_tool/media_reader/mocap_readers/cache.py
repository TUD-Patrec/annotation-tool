import io
import logging
import math
import threading
from typing import Optional

import numpy as np


class CompressedArray:
    def __init__(self, arr: np.ndarray, compress):
        self._compressed = compress

        if compress:
            compressed_data = io.BytesIO()
            np.savez_compressed(compressed_data, arr)
            logging.debug(
                f"Compressed {arr.nbytes / 1024} KB to {compressed_data.getbuffer().nbytes / 1024} KB"
            )
            self._arr: io.BytesIO = compressed_data
        else:
            self._arr: np.ndarray = arr

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


class ArrayCache(object):
    def __init__(self, max_size_mb: int = 256, compress=False):
        self._cache = []
        self._lock = threading.Lock()
        self._compress = compress

        self._max_size_bytes = max_size_mb * 2**20
        self._current_size_bytes = 0

        logging.debug(f"Initialized {self}")

    def __len__(self):
        return len(self._cache)

    def __repr__(self):
        _len = len(self._cache)
        _size_mb = math.ceil(self._current_size_bytes / 2**20)
        _max_size_mb = math.ceil(self._max_size_bytes / 2**20)
        return f"{self.__class__.__name__}(N={_len}, max_size={_max_size_mb}MB, filled={_size_mb / _max_size_mb * 100:.2f}%, compress={self._compress})"

    def __contains__(self, _key):
        return _key in [k for k, _ in self._cache]

    def __getitem__(self, _key):
        with self._lock:
            for k, data in self._cache:
                if k == _key:
                    _data = data.data
                    self._cache.remove((k, data))
                    self._cache.append((k, data))  # move to end
                    return _data.copy()
        raise KeyError(f"Key {_key} not found in cache.")

    def __setitem__(self, _key, _value):
        self.__put__(_key, _value)

    def __put__(self, _key, _data: np.ndarray) -> None:
        assert isinstance(_data, np.ndarray), "Data must be a numpy array."

        with self._lock:
            compressed_data = CompressedArray(_data, self._compress)

            if compressed_data.nbytes > 0.9 * self._max_size_bytes:
                logging.warning(
                    f"Object with key={_key} is larger than the cache size. Skipping."
                )
                return

            self._current_size_bytes += compressed_data.nbytes
            self._evict()
            self._cache.append((_key, compressed_data))

        logging.debug(f"Added {_key} to cache -> {self}")

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

    def get(self, _key, _default=None) -> Optional[np.ndarray]:
        try:
            return self[_key]
        except KeyError:
            return _default

    def set_max_size(self, _max_size_kb: int):
        with self._lock:
            self._max_size_bytes = _max_size_kb * 1024
            self._evict()

    def set_compress(self, _compress: bool):
        with self._lock:
            self._compress = _compress


_mocap_cache = ArrayCache()  # Singleton


def get_cache() -> ArrayCache:
    return _mocap_cache
