import os

from qgis.PyQt.QtCore import QDateTime, QDate, QTime


def version():
    metadata = os.path.abspath(os.path.join(__file__, '..', 'metadata.txt'))
    with open(metadata, encoding='utf-8') as f:
        for line in f.readlines():
            if line.startswith('version='):
                return line.split('=')[1].strip()


def utilsMsecToDateTime(msec: int) -> QDateTime:
    return QDateTime(QDate(1970, 1, 1), QTime(0, 0, 0)).addMSecs(int(msec))
