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
        self._instance = None

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        if self._instance is None:
            self._instance = self._decorated()
        return self._instance

    def __call__(self):
        raise TypeError("Singletons must be accessed through `instance()`.")

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
