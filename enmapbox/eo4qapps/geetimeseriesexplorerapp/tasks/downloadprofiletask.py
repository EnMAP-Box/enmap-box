from math import nan
from os.path import exists
from typing import Optional, List

from enmapboxprocessing.utils import Utils
from qgis.core import QgsTask, QgsMessageLog, Qgis
from typeguard import typechecked


@typechecked
class DownloadProfileTask(QgsTask):

    def __init__(
            self, filename: Optional[str], eePoint, eeCollection, scale: float, offsets: List[float],
            scales: List[float], limit: Optional[int]
    ):
        QgsTask.__init__(self, 'Download profile task', QgsTask.CanCancel)
        self.filename = filename
        self.eePoint = eePoint
        self.eeCollection = eeCollection
        self.scale = scale
        self.offsets = offsets
        self.scales = scales
        self.limit = limit
        self.data_: Optional[List] = None
        self.exception: Optional[Exception] = None

    def run(self):
        try:

            if self.filename is not None:
                self.alreadyExists = exists(self.filename)
            else:
                self.alreadyExists = False

            if self.alreadyExists:
                return True

            if self.filename is not None and exists(self.filename):  # if file already exists,
                return True  # we do nothing

            eeCollection = self.eeCollection.filterBounds(self.eePoint)
            if self.limit is not None:
                eeCollection = eeCollection.limit(self.limit)

            self.data_ = eeCollection.getRegion(self.eePoint, scale=self.scale).getInfo()

            # scale data
            for i, (offset, scale) in enumerate(zip(self.offsets, self.scales), 4):
                if offset != 0 or scale != 1:
                    for values in self.data_[1:]:
                        value = values[i]
                        if value is None:
                            value = nan
                        else:
                            value = value * scale + offset
                        values[i] = value

            if self.filename is not None:
                Utils.jsonDump(self.data_, self.filename)

        except Exception as e:
            self.exception = e
            return False

        return True

    def finished(self, result):
        if self.isCanceled():
            return
        elif not result:
            # raise self.exception
            QgsMessageLog.logMessage(
                str(self.exception), tag="GEE Time Series Explorer", level=Qgis.MessageLevel.Critical
            )

        if self.filename is not None:
            if self.alreadyExists:
                QgsMessageLog.logMessage(
                    f'already exists: {self.filename}', tag="GEE Time Series Explorer", level=Qgis.Success
                )
            else:
                QgsMessageLog.logMessage(
                    f'downloaded: {self.filename}', tag="GEE Time Series Explorer", level=Qgis.Success
                )

    def data(self) -> Optional[List]:
        if self.data_ is None:
            self.data_ = Utils.jsonLoad(self.filename)  # use cached version
        return self.data_
