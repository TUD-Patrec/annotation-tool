import abc
import functools
import logging
import os
from typing import List, Optional, Type, Union

import appdirs
from fcache.cache import FileCache

__application_name__ = "annotation-tool"
__application_path__ = appdirs.user_data_dir(__application_name__, __application_name__)
__application_cache_path__ = appdirs.user_cache_dir(
    __application_name__, __application_name__
)

__file_cache__ = FileCache(
    __application_name__, flag="c", app_cache_dir=__application_cache_path__
)
__cache_directory__ = __file_cache__.cache_dir

if logging.getLogger().isEnabledFor(logging.DEBUG):
    logging.debug(f"Cache directory: {__cache_directory__}")
else:
    print(f"Cache directory: {__cache_directory__}")


def get_dir() -> str:
    """
    Returns the path to the cache directory.
    """
    return __cache_directory__


def application_path() -> str:
    """
    Returns the path to the root directory of the cache.
    """
    return __application_path__


def get_size_in_bytes() -> int:
    """
    Returns the size of the cache in bytes.
    """
    return sum(
        os.path.getsize(os.path.join(__cache_directory__, f))
        for f in os.listdir(__cache_directory__)
    )


def get_next_id() -> str:
    _next_id = max([int(x) for x in __file_cache__.keys()], default=0) + 1

    # closure
    def get_id():
        nonlocal _next_id
        _next_id += 1
        return _next_id

    return str(get_id())


def write(obj: object) -> None:
    """
    Writes the object to the cache.

    Args:
        obj: The object to write.

    Raises:
        TypeError: If the object cannot be cached (i.e. it does not use the @cached decorator).
    """
    try:
        cache_id = obj.cache_id
    except AttributeError:
        raise TypeError(f"Cannot cache object of type {type(obj)}")
    if cache_id is None:
        obj.cache_id = get_next_id()  # only needed for the decorator
    __file_cache__[obj.cache_id] = obj
    __file_cache__.sync()


def delete(obj: object) -> None:
    """
    Deletes the object from the cache.

    Args:
        obj: The object to delete.
    """
    if not hasattr(obj, "cache_id"):
        raise TypeError(f"Cannot delete object of type {type(obj)}")
    try:
        del __file_cache__[obj.cache_id]
        __file_cache__.sync()
    except KeyError:
        pass


def get_by_type(x: Union[Type, str]) -> List[object]:
    """
    Returns a list of all objects of type x in the cache.

    Args:
        x: The type of the objects to return.

    """

    cls_name = x if isinstance(x, str) else x.__name__
    return [
        obj for obj in __file_cache__.values() if obj.__class__.__name__ == cls_name
    ]


def get_by_id(x: int) -> Optional[object]:
    """
    Returns the object with the given id from the cache.

    Args:
        x: The id of the object to return.

    Returns:
        The object with the given id or None if no object with the given id exists.
    """
    try:
        return __file_cache__[x]
    except KeyError:
        return None


def wrap_setattr(func):
    @functools.wraps(func)
    def wrapper(self, key, value):
        func(self, key, value)
        if key != "_id":  # TODO check if this is necessary, _id is not used anymore
            write(self)

    return wrapper


def get_all_of_class(cls) -> List[object]:
    """
    Returns a list of all objects of type cls in the cache.
    The elements are sorted by their cache_id.
    """
    all_ = get_by_type(cls)
    all_.sort(key=lambda x: x.cache_id)
    return all_


def del_all_of_class(cls) -> None:
    """
    Deletes all objects of type cls from the cache.
    """
    for obj in get_by_type(cls):
        delete(obj)


def get_all() -> List[object]:
    """
    Returns a list of all objects in the cache.
    """
    all_ = list(__file_cache__.values())
    all_.sort(key=lambda x: int(x.cache_id))
    return all_


def clear() -> None:
    """
    Clears the cache.
    """
    __file_cache__.clear()
    __file_cache__.sync()


def cached(cls):
    """
    Decorator for classes that should be cached.
    Updating an attribute of the class will automatically update the object in the cache.

    Adding a few class-methods:
        delete(self) -> None
            Deletes the object from the cache.
        sync(self) -> None
            Writes the object to the cache.
        synchronize(self) -> None
            Writes the object to the cache. (alias for sync)

    Args:
        cls: The class to decorate.
    """
    cls.cache_id = None
    cls.__setattr__ = wrap_setattr(cls.__setattr__)
    cls.delete = delete
    cls.sync = write
    cls.synchronize = write
    cls.get_all = functools.partial(get_all_of_class, cls.__name__)
    cls.del_all = functools.partial(del_all_of_class, cls.__name__)

    return cls


class Cachable(abc.ABC):
    """
    Abstract base class for cachable objects.
    """

    __cache_id__: str

    def __init__(self):
        self.__cache_id__ = get_next_id()  # init cache_id

    def delete(self) -> None:
        """
        Deletes the object from the cache.
        """
        delete(self)

    def sync(self) -> None:
        """
        Writes the object to the cache.
        """
        write(self)

    def synchronize(self) -> None:
        """
        Writes the object to the cache. (alias for sync)
        """
        write(self)

    @classmethod
    def get_all(cls) -> List[object]:
        """
        Returns a list of all objects of type cls in the cache.
        The elements are sorted by their cache_id.
        """
        return get_all_of_class(cls)

    @classmethod
    def del_all(cls) -> None:
        """
        Deletes all objects of type cls from the cache.
        """
        del_all_of_class(cls)

    @property
    def cache_id(self) -> str:
        return self.__cache_id__

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if self.cache_id:
            write(self)
        else:
            logging.warning("cache_id is not set yet.")
