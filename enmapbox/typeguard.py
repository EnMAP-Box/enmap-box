# typeguard is an optional dependency, so it shouldn't be import directly (see #345)
from functools import partial

try:  # try to import some members we usually use
    from typeguard import typechecked, check_type
except (ImportError, ModuleNotFoundError):  # or mock them
    def typechecked(func=None, *, always=False, _localns=None):
        if func is None:
            return partial(typechecked, always=always, _localns=_localns)
        return func

    def check_type(*args, **kwds):
        pass

# make typeguard classes / mocks searchable for IDE
typechecked = typechecked
check_type = check_type
