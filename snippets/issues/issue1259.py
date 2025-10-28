import datetime
import unittest
from pathlib import Path

from qgis.core import QgsRasterLayer

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from enmapbox.testing import TestCase, start_app
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import SensorProducts

start_app()
initAll()
path_tanager = Path(SensorProducts.Tanager.basic_radiance)


class TestIssueXSlowReading(TestCase):

    @unittest.skipIf(not path_tanager.is_file(), f'File does not exist: {path_tanager}')
    def test_issue_x_slowreading(self):
        path_toa = f'HDF5:"{path_tanager.as_posix()}"://HDFEOS/SWATHS/HYP/Data_Fields/toa_radiance'

        TIMES = {}
        t0 = datetime.datetime.now()

        def getTime(msg: str):
            nonlocal t0
            TIMES[msg] = datetime.datetime.now() - t0
            t0 = datetime.datetime.now()

        lyr = QgsRasterLayer(path_toa, 'tanager')
        getTime('Open Layer')
        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(lyr)
        wl1 = prop.wavelengths()
        # wlu1 = prop.wavelengthUnits()
        print(wl1)
        # print(wlu1)
        getTime('Read spectral properties (QPS)')

        reader = RasterReader(lyr)
        wl2 = []
        wlu2 = []
        for b in range(1, lyr.bandCount() + 1):
            wl2.append(reader.wavelength(b, raw=True))
            # wlu2.append(reader.wavelengthUnits(b))
        getTime('Read spectral properties (RasterReader)')

        for msg, dt in TIMES.items():
            print(f'{msg}: {dt.total_seconds():.3f}s')
