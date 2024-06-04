from typing import Tuple, Iterable, Dict, Optional

from enmapbox.qgispluginsupport.qps.speclib.core import is_profile_field
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import decodeProfileValueDict
from enmapbox.typeguard import typechecked
from qgis.core import QgsGeometry, QgsVectorLayer


@typechecked
class LibraryReader(object):

    def __init__(self, library: QgsVectorLayer):
        self.library = library

    def data(self) -> Iterable[Tuple[Dict, Optional[QgsGeometry]]]:

        fields = [self.library.fields().at(i) for i in range(self.library.fields().count())]
        fieldNames = [field.name() for field in fields]
        profileFieldIndices = [i for i, field in enumerate(fields) if is_profile_field(field)]

        for feature in self.library.getFeatures():
            geometry = feature.geometry()
            if geometry.isNull():
                geometry = None
            attributes = feature.attributes()
            for i in profileFieldIndices:
                attributes[i] = decodeProfileValueDict(attributes[i])
            values = dict(zip(fieldNames, attributes))
            yield values, geometry
