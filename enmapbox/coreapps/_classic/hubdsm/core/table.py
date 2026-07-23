from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Table(object):
    recarray: np.recarray

    def __getitem__(self, item) -> 'Table':
        return self.recarray.__getitem__(item)

    def __len__(self):
        return self.recarray.__len__()

    def __getattr__(self, item):
        return self.recarray[item]

    @property
    def dtype(self):
        return self.recarray.dtype

    def array(self, dtype=None) -> np.ndarray:
        array = np.array([self.recarray[name] for name in self.recarray.dtype.names], dtype=dtype)
        return array
