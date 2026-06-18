from typing import List

from enmapbox.typeguard import typechecked
from enmapboxprocessing.librarywriter import LibraryWriter
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsVectorLayer, Qgis, QgsWkbTypes


@typechecked
class LibraryDriver(object):

    def create(
            self, name: str = None, wkbType: Qgis.WkbType = None, crs: QgsCoordinateReferenceSystem = None
    ) -> LibraryWriter:

        if name is None:
            name = 'Spectral Library'

        if wkbType is None:
            wkbType = Qgis.WkbType.Point

        if crs is None:
            crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)

        provider = 'memory'
        path = f'{QgsWkbTypes.displayString(wkbType)}?crs={crs.authid()}'
        options = QgsVectorLayer.LayerOptions(loadDefaultStyle=True, readExtentFromXml=True)

        library = QgsVectorLayer(path, name, provider, options=options)
        library.setCustomProperty('skipMemoryLayerCheck', 1)
        assert library.isValid()

        return LibraryWriter(library)

    def createFromData(
            self, data: List[dict], geometries: List[QgsGeometry] = None, name: str = None,
            wkbType: Qgis.WkbType = None, crs: QgsCoordinateReferenceSystem = None
    ) -> LibraryWriter:

        if geometries is None:
            geometries = [None] * len(data)
        else:
            if wkbType is None:
                wkbType = geometries[0].wkbType()
            if crs is None:
                crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)

        # init library by parsing first element
        writer = self.create(name, wkbType, crs)
        values = data[0]
        for fieldName, value in values.items():
            if isinstance(value, dict):
                writer.addProfileAttribute(fieldName)
            else:
                writer.addAttribute(fieldName, QVariant(value).type())

        # add data
        for values, geometry in zip(data, geometries):
            writer.addFeature(values, geometry)

        return writer
