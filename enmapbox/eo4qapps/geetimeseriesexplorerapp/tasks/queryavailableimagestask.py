from typing import List, Optional

from enmapbox.utils import importEarthEngine
from geetimeseriesexplorerapp.utils import utilsMsecToDateTime
from qgis.core import QgsTask
from qgis.gui import QgsMessageBar
from typeguard import typechecked


@typechecked
class QueryAvailableImagesTask(QgsTask):
    """Query available images at location."""
    header: List[str]
    data: List[List[str]]

    def __init__(self, eeCollection, eePoint, limit: int, messaqeBar: Optional[QgsMessageBar]):
        QgsTask.__init__(self, 'Query available images at location', QgsTask.CanCancel)
        self.eeCollection = eeCollection
        self.eePoint = eePoint
        self.limit = limit
        self.messaqeBar = messaqeBar
        self.exception: Optional[Exception] = None

    def run(self):
        eeImported, ee = importEarthEngine(False)

        try:
            properties_ = sorted(self.eeCollection.first().propertyNames().getInfo())
            properties = ['system:index', 'system:time_start']
            properties.extend([p for p in properties_ if not p.startswith('system:')])
            properties.extend([p for p in properties_ if p.startswith('system:')])

            eeCollection = self.eeCollection.filterBounds(self.eePoint)
            infos = eeCollection.toList(self.limit).map(lambda eeImage: [ee.Image(eeImage).get(key)
                                                                         for key in properties]
                                                        ).getInfo()

            self.header = ['Available Images', 'Acquisition Time'] + properties[2:]
            self.data = list()

            if len(infos) == 0:
                return True

            # format content to enable correct sorting
            propertyFormat = dict()
            for i, property in enumerate(properties):
                if i < 2:
                    continue
                if any([isinstance(row[i], float) for row in infos if row[i] is not None]):
                    n1 = len(str(max([int(row[i]) for row in infos if row[i] is not None])))
                    n2 = max([len(str(row[i]).split('.')[1]) for row in infos if '.' in str(row[i])])
                    n = n1 + n2 + 1
                    propertyFormat[property] = '{:' + str(n) + '.' + str(n2) + 'f}'  # .format(value)
                elif all([isinstance(row[i], int) for row in infos]):
                    n = len(str(max([row[i] for row in infos])))
                    propertyFormat[property] = '{:' + str(n) + '.0f}'

            for i, values in enumerate(infos):
                row = list()
                imageId = values[0]
                msec = values[1]
                timestamp = utilsMsecToDateTime(msec).toString('yyyy-MM-ddThh:mm:ss')
                row.append(imageId)
                row.append(timestamp)
                for k, value in enumerate(values[2:], 2):
                    property = properties[k]
                    if value is None:
                        value = 'None'
                    else:
                        value = propertyFormat.get(property, '{}').format(value)
                    row.append(value)
                self.data.append(row)

        except Exception as e:
            self.exception = e
            return False

        return True

    def finished(self, result):
        if self.isCanceled():
            return
        elif not result:
            raise self.exception
