from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from _classic.hubdsm.core.shape import GridShape


def callbackStartDefault(name: str) -> datetime:
    t0 = datetime.now()
    t0str = str(t0).replace(' ', 'T').split('.')[0]
    print(f'[{name[0].upper()}{name[1:]}] started at {t0str}', end=' 0%..', flush=True)
    return t0


def callbackProgressDefault(i: int, n: int):
    print(f'{int(round(i / n * 100))}%', end='..', flush=True)


def callbackFinishDefault(name: str, t0: datetime) -> datetime:
    t1 = datetime.now()
    td = t1 - t0
    t1str = str(t1).replace(' ', 'T').split('.')[0]
    tdstr = ':'.join(v + u for v, u in zip(str(td).split(':'), ('h', 'm', 's')))
    print(f'\n[{name[0].upper()}{name[1:]}] finished in {tdstr} at {t1str}', flush=True)
    return t1


@dataclass
class ProcessingOptions(object):
    shape: GridShape = None
    callbackStart: Callable[[str], datetime] = callbackStartDefault
    callbackProgress: Callable[[int, int, str], None] = callbackProgressDefault
    callbackFinish: Callable[[str, int, int, str], datetime] = callbackFinishDefault

    def __post_init__(self):
        assert isinstance(self.shape, (GridShape, type(None)))
        assert isinstance(self.callbackStart, Callable)
        assert isinstance(self.callbackProgress, Callable)

    def getShape(self, default: GridShape):
        if self.shape is None:
            return default
        else:
            return self.shape
