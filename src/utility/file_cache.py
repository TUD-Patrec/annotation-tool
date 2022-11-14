import logging

from fcache.cache import FileCache

_file_cache = FileCache("annotation-tool", flag="cs")

logging.info(f"Cache directory: {_file_cache.cache_dir}")

# check if key "ID" exists
if "next_id" not in _file_cache:
    _file_cache["next_id"] = 0


def write(obj) -> None:
    from src.data_model import Dataset, GlobalState, Settings

    if not hasattr(obj, "_id") or obj._id is None:
        obj._id = _file_cache["next_id"]
        _file_cache["next_id"] += 1
    if isinstance(obj, Settings):
        _file_cache["settings"] = Settings.instance()
    elif isinstance(obj, GlobalState):
        _file_cache["global_state"][obj._id] = obj
    elif isinstance(obj, Dataset):
        _file_cache["dataset"][obj._id] = obj
    else:
        raise TypeError(f"Cannot cache object of type {type(obj)}")


def get_settings():
    return _file_cache["settings"]


def get_global_states():
    return (_file_cache["global_state"][key] for key in _file_cache["global_state"])


def get_datasets():
    return (_file_cache["dataset"][key] for key in _file_cache["dataset"])


class Cachable:
    def __init__(self):
        print("Cachable init")
        self._id = None

    def __setattr__(self, key, value):
        """Overwrite __setattr__ to write to cache on every change"""
        super().__setattr__(key, value)

        if key != "_id":
            print(f"{key = } Writing {self} to cache")
            write(self)
