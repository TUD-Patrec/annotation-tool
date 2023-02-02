from contextlib import suppress
from functools import wraps
import inspect
import typing


def accepts_m(*types) -> typing.Callable:
    """Check parameter types for a class-method.

    Returns:
        Callable: Wrapped method that is now typesafe on its inputs.
    """
    return accepts(object, *types)


def accepts(*types) -> typing.Callable:
    """Check parameter types for a function.

    Returns:
        Callable: Wrapped function that is now typesafe on its inputs.
    """

    def check_accepts(f):
        #  assert len(types) == f.func_code.co_argcount
        assert len(types) == f.__code__.co_argcount, f"{f.__code__.co_argcount = }"

        def new_f(*args, **kwds):
            for (a, t) in zip(args, types):
                assert isinstance(a, t), "arg %r does not match %s" % (a, t)
            return f(*args, **kwds)

        # new_f.func_name = f.func_name
        new_f.__name__ = f.__name__
        return new_f

    return check_accepts


def returns(rtype: typing.Type) -> typing.Callable:
    """Check return types of a function.

    Args:
        rtype (Type): Type of the return value.

    Returns:
        Callable: Wrapped function which return value confirm to
        the type-declaration.
    """

    def check_returns(f):
        def new_f(*args, **kwds):
            result = f(*args, **kwds)
            assert isinstance(result, rtype), "return value %r does not match %s" % (
                result,
                rtype,
            )
            return result

        # new_f.func_name = f.func_name
        new_f.__name__ = f.__name__
        return new_f

    return check_returns


# @accepts(int, (int,float))
# @returns((int,float))
# def func(arg1, arg2):
#     return arg1 * arg2


def enforce_types(callable):
    spec = inspect.getfullargspec(callable)

    def check_types(*args, **kwargs):
        parameters = dict(zip(spec.args, args))
        parameters.update(kwargs)
        for name, value in parameters.items():
            with suppress(KeyError):  # Assume un-annotated parameters can be any type
                type_hint = spec.annotations[name]
                if isinstance(type_hint, typing._SpecialForm):
                    # No check for typing.Any, typing.Union,
                    # typing.ClassVar (without parameters)
                    continue
                try:
                    actual_type = type_hint.__origin__
                except AttributeError:
                    # In case of non-typing types (such as <class 'int'>, for instance)
                    actual_type = type_hint
                # In Python 3.8 one would replace the try/except with
                # actual_type = typing.get_origin(type_hint) or type_hint
                if isinstance(actual_type, typing._SpecialForm):
                    # case of typing.Union[…] or typing.ClassVar[…]
                    actual_type = type_hint.__args__

                if not isinstance(value, actual_type):
                    raise TypeError(
                        "Unexpected type for '{}' (expected {} but found {})".format(
                            name, type_hint, type(value)
                        )
                    )

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            check_types(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    if inspect.isclass(callable):
        callable.__init__ = decorate(callable.__init__)
        return callable

    return decorate(callable)


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError("Singletons must be accessed through `instance()`.")

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
