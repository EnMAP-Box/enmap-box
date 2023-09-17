# https://github.com/EnMAP-Box/enmap-box/files/12475606/data.zip
import pathlib

from enmapbox.qgispluginsupport.qps.speclib.core import profile_field_list
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import prepareProfileValueDict, encodeProfileValueDict, \
    decodeProfileValueDict
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.testing import start_app, EnMAPBoxTestCase, TestObjects
from qgis.core import QgsVectorLayer, QgsFeature
from qgis.core import edit

PATH_EXAMPLE = pathlib.Path(__file__).parent / 'data' / 'sentinel2a_msi.geojson'
start_app()


class TestIssue581(EnMAPBoxTestCase):

    def test_loadProfiles(self):

        assert PATH_EXAMPLE.is_file()

        if True:
            speclib = QgsVectorLayer(PATH_EXAMPLE.as_posix())
            self.assertTrue(speclib.isValid())
        else:
            x = [1, 2, 3, 4, 5]
            y = [0.0, 1, 2, 0.5, 0]
            d = prepareProfileValueDict(x=x, y=y)

            sl = TestObjects.createSpectralLibrary(n=0)

            pfield = profile_field_list(sl)[0]
            with edit(sl):
                f = QgsFeature(sl.fields())
                dump = encodeProfileValueDict(d, encoding=pfield)
                p2 = decodeProfileValueDict(dump)
                f.setAttribute(pfield.name(), dump)
                p3 = decodeProfileValueDict(f.attribute(pfield.name()))
                sl.addFeature(f)
            speclib = sl

            p4 = decodeProfileValueDict(list(speclib.getFeatures())[0].attribute(pfield.name()))

        slw = SpectralLibraryWidget(speclib=speclib)

        self.showGui(slw)
