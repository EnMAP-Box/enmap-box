import datetime
import unittest
from pathlib import Path

from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import QgsProject
from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.layerproperties import showLayerPropertiesDialog
from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties, \
    SpectralPropertyKeys
from enmapbox.testing import TestCase, start_app
from qgis.core import QgsRasterLayer
from osgeo import gdal

from rasterlayerstylingapp import RasterLayerStylingPanel

start_app()
initAll()
path_tanager = Path(r'/home/jakimowb/Downloads/20250510_005001_00_4001_basic_radiance.h5')

class TestIssue1259SlowReading(TestCase):

    @unittest.skipIf(not path_tanager.is_file(), f'File does not exist: {path_tanager}')
    def test_issue_1259_slowreading(self):
        path_toa = f'HDF5:"{path_tanager.as_posix()}"://HDFEOS/SWATHS/HYP/Data_Fields/toa_radiance'

        TIMES = {}
        t0 = datetime.datetime.now()
        def getTime(msg: str):
            nonlocal t0
            TIMES[msg] = datetime.datetime.now() - t0
            t0 = datetime.datetime.now()

        ds = gdal.Open(path_toa)
        for b in range(1, ds.RasterCount+1):
            band = ds.GetRasterBand(b)
            s = ""
        lyr = QgsRasterLayer(path_toa, 'tanager')
        getTime('Open Layer')

        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(lyr)
        getTime('Read spectral properties (QPS)')

        reader = RasterReader(lyr)
        wl2 = []
        wlu2 = []
        for b in range(1, lyr.bandCount()+1):
            wl2.append(reader.wavelength(b))
            wlu2.append(reader.wavelengthUnits(b))
        getTime('Read spectral properties (RasterReader')



        dialog = showLayerPropertiesDialog(lyr, modal=False)
        getTime('Open properties dialog')

        for msg, dt in TIMES.items():
            print(f'{msg}: {dt.total_seconds():.3f}s')

        # self.assertEqual(wl1, wl2)
        # self.assertEqual(wlu1, wlu2)

        widgets = [dialog]
        self.showGui(widgets)
        del lyr
        QgsProject.instance().removeAllMapLayers()
        s = ""