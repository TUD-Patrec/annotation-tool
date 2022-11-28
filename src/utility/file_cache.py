import functools
from typing import List, Optional, Type, Union

from fcache.cache import FileCache

_file_cache = FileCache("annotation-tool", flag="c")
_cache_directory = _file_cache.cache_dir
print(f"Cache directory: {_cache_directory}")


def get_next_id() -> str:
    _next_id = max([int(x) for x in _file_cache.keys()], default=0) + 1

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
    if not hasattr(obj, "cache_id"):
        raise TypeError(f"Object of type {type(obj)} is not cachable.")
    if obj.cache_id is None:
        obj.cache_id = get_next_id()
    _file_cache[obj.cache_id] = obj
    _file_cache.sync()


def delete(obj: object) -> None:
    """
    Deletes the object from the cache.

    Args:
        obj: The object to delete.
    """
    if not hasattr(obj, "cache_id"):
        raise TypeError(f"Cannot delete object of type {type(obj)}")
    try:
        del _file_cache[obj.cache_id]
        _file_cache.sync()
    except KeyError:
        pass


def get_by_type(x: Union[Type, str]) -> List[object]:
    """
    Returns a list of all objects of type x in the cache.

    Args:
        x: The type of the objects to return.

    """

    cls_name = x if isinstance(x, str) else x.__name__
    return [obj for obj in _file_cache.values() if obj.__class__.__name__ == cls_name]


def get_by_id(x: int) -> Optional[object]:
    """
    Returns the object with the given id from the cache.

    Args:
        x: The id of the object to return.

    Returns:
        The object with the given id or None if no object with the given id exists.
    """
    try:
        return _file_cache[x]
    except KeyError:
        return None


def wrap_setattr(func):
    @functools.wraps(func)
    def wrapper(self, key, value):
        func(self, key, value)
        if key != "_id":
            write(self)

    return wrapper


def get_all(cls) -> List[object]:
    """
    Returns a list of all objects of type cls in the cache.
    The elements are sorted by their cache_id.
    """
    all = get_by_type(cls)
    all.sort(key=lambda x: x.cache_id)
    return all


def del_all(cls) -> None:
    """
    Deletes all objects of type cls from the cache.
    """
    for obj in get_by_type(cls):
        delete(obj)


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
    cls.get_all = functools.partial(get_all, cls.__name__)
    cls.del_all = functools.partial(del_all, cls.__name__)

    return cls
