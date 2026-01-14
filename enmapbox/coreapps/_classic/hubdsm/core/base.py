import inspect
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass(frozen=True)
class DataClassIterable(object):

    def __iter__(self):
        return self.__dict__.values().__iter__()

    def __getitem__(self, item):
        return tuple(self.__dict__.values())[item]

    def __len__(self):
        return len(self.__dict__)

    @classmethod
    def fromIterable(cls, iterable: Iterable):
        parameters: List[inspect.Parameter] = list(inspect.signature(cls.__init__).parameters.values())[1:]
        values = list()
        for parameter, value in zip(parameters, iterable):
            dtype = parameter.annotation
            if isinstance(dtype, str):
                dtype = eval(dtype)
            values.append(dtype(value))

        return cls(*values)


@dataclass(frozen=True)
class DataClassArray(DataClassIterable):
    _GLOBAL_ARRAY_CACHE = dict()

    def __del__(self):
        self._GLOBAL_ARRAY_CACHE.pop(self, None)

    @property
    def __array_interface__(self):
        array = np.array(tuple(self))
        self._GLOBAL_ARRAY_CACHE[self] = array
        return array.__array_interface__

    @property
    def _(self) -> np.ndarray:
        """Return as array."""
        return np.array(self)