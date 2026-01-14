from dataclasses import dataclass
from random import randint

from _classic.hubdsm.core.base import DataClassIterable


@dataclass(frozen=True)
class Color(DataClassIterable):
    red: int = 0
    green: int = 0
    blue: int = 0
    alpha: int = 255

    @classmethod
    def fromRandom(cls):
        return cls(red=randint(0, 255), green=randint(0, 255), blue=randint(0, 255))
