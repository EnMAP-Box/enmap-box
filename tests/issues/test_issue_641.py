from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.io.rastersources import RasterLayerSpectralLibraryIO, \
    RasterLayerSpectralLibraryImportWidget
from enmapboxprocessing.testcase import TestCase
from qgis.core import QgsRasterLayer
from qgis.core import QgsVectorLayer


class Issue641Tests(TestCase):

    def test_issue641(self):
        initAll()
        from enmapbox.exampledata import enmap, landcover_point
        rl = QgsRasterLayer(enmap)
        vl = QgsVectorLayer(landcover_point)

        io = RasterLayerSpectralLibraryIO()

        w = RasterLayerSpectralLibraryImportWidget()
        fields = w.sourceFields()
        for d in io.readRasterVector(rl, vl, fields):
            d = ""
