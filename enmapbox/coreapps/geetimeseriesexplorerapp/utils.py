import os

from qgis.PyQt.QtCore import QDateTime, QDate

from typeguard import typechecked


def version():
    metadata = os.path.abspath(os.path.join(__file__, '..', 'metadata.txt'))
    with open(metadata, encoding='utf-8') as f:
        for line in f.readlines():
            if line.startswith('version='):
                return line.split('=')[1].strip()


@typechecked
def utilsMsecToDateTime(msec: int) -> QDateTime:
    return QDateTime(QDate(1970, 1, 1)).addMSecs(int(msec))
