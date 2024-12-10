from typing import List

from enmapbox.qgispluginsupport.qps.speclib.core import create_profile_field
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import ProfileEncoding
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import prepareProfileValueDict, \
    encodeProfileValueDict
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, edit, QgsGeometry


@typechecked
class LibraryWriter(object):

    def __init__(self, library: QgsVectorLayer):
        self.library = library

    def addProfileAttribute(self, name: str, encoding=ProfileEncoding.Text):
        with edit(self.library):
            self.library.beginEditCommand('Add profile attribute')
            SpectralLibraryUtils.addAttribute(self.library, create_profile_field(name, None, encoding))
            self.library.endEditCommand()

    def addAttribute(self, name: 'str', type_: QVariant.Type):
        self.library.startEditing()
        self.library.addAttribute(QgsField(name, type_))
        self.library.commitChanges()

    def addFeature(self, values: dict, geometry: QgsGeometry = None):

        with edit(self.library):
            feature: QgsFeature = QgsFeature(self.library.fields())
            if geometry is not None:
                feature.setGeometry(geometry)
            for fieldName, value in values.items():
                if isinstance(value, dict):  # is a profile attribute
                    fieldIndex = self.library.fields().indexFromName(fieldName)

                    field = self.library.fields().field(fieldIndex)
                    profileDict = prepareProfileValueDict(
                        value.get('x'), value.get('y'), value.get('xUnit'), value.get('yUnit'), value.get('bbl')
                    )
                    dump = encodeProfileValueDict(profileDict, encoding=field)
                    feature.setAttribute(fieldName, dump)
                else:
                    feature.setAttribute(fieldName, value)
            assert self.library.addFeature(feature)

    def writeToSource(self, filename: str) -> List[str]:
        return SpectralLibraryUtils.writeToSource(self.library, filename)
