from typing import List

from enmapbox.qgispluginsupport.qps.qgisenums import QGIS_WKBTYPE

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import ProfileEncoding
from qgis.core import QgsVectorLayer


class LibraryUtils(object):

    @staticmethod
    def createSpectralLibrary(
            profileFields: List[str],
            name='SpectralLibrary',
            encoding: ProfileEncoding = ProfileEncoding.Json,
            wkbType: QGIS_WKBTYPE = QGIS_WKBTYPE.Point
    ) -> QgsVectorLayer:
        return SpectralLibraryUtils.createSpectralLibrary(profileFields, name, encoding, wkbType)
