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
        assert (
            len(types) == f.__code__.co_argcount
        ), f"{f.__code__.co_argcount = } != {len(types) = }"

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
            assert isinstance(
                result, rtype
            ), f'return value {result} does not match {rtype} in function "{f.__name__}"'
            return result

        # new_f.func_name = f.func_name
        new_f.__name__ = f.__name__
        return new_f

    return check_returns
