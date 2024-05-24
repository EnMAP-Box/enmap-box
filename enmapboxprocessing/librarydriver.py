from typing import List

from enmapbox.typeguard import typechecked
from enmapboxprocessing.librarywriter import LibraryWriter
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorLayer
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils


@typechecked
class LibraryDriver(object):

    def create(self, name: str) -> LibraryWriter:
        library: QgsVectorLayer = SpectralLibraryUtils.createSpectralLibrary([], name)
        return LibraryWriter(library)

    def createFromData(self, name: str, data: List[dict], geometries: List = None) -> LibraryWriter:
        if geometries is not None:
            raise NotImplementedError()

        # init library by parsing first element
        writer = self.create(name)
        values = data[0]
        for fieldName, value in values.items():
            if isinstance(value, dict):
                writer.addProfileAttribute(fieldName)
            else:
                writer.addAttribute(fieldName, QVariant(value).type())

        # add data
        for values in data:
            writer.addFeature(values)

        return writer
