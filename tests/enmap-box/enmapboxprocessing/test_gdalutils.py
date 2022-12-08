from osgeo import gdal

from enmapboxprocessing.gdalutils import GdalUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap


class TestGdalUtils(TestCase):

    def test_stackSingleBandVrts(self):
        # create single band VRT for NIR, SWIR1 and RED bands
        filename1 = self.filename('nir.vrt')
        gdal.Translate(filename1, enmap, bandList=[62], format='VRT')
        filename2 = self.filename('swir1.vrt')
        gdal.Translate(filename2, enmap, bandList=[116], format='VRT')
        filename3 = self.filename('red.vrt')
        gdal.Translate(filename3, enmap, bandList=[39], format='VRT')

        # stack bands
        filename = self.filename('stack.vrt')
        GdalUtils.stackVrtBands(filename, [filename1, filename2, filename3], [1, 1, 1])

        self.assertArrayEqual(
            RasterReader(enmap).array(bandList=[62, 116, 39]),
            RasterReader(filename).array(),
        )

    def test_stackMultiBandVrts(self):
        # create VRT copy with all bands
        filename1 = self.filename('enmap.vrt')
        gdal.Translate(filename1, enmap, format='VRT')

        # stack bands
        filename = self.filename('stack.vrt')
        GdalUtils.stackVrtBands(filename, [filename1, filename1, filename1], [62, 116, 39])

        self.assertArrayEqual(
            RasterReader(enmap).array(bandList=[62, 116, 39]),
            RasterReader(filename).array(),
        )

    def test_stackMultiBandVrts_withRelativeInputs(self):

        gdal.Translate(self.filename('enmap.tif'), enmap)

        # create VRT copy with all bands
        filename1 = self.filename('enmap.vrt')
        gdal.Translate(filename1, self.filename('enmap.tif'), format='VRT')

        # stack bands
        filename = self.filename('stack.vrt')
        GdalUtils.stackVrtBands(filename, [filename1, filename1, filename1], [62, 116, 39])

        self.assertArrayEqual(
            RasterReader(enmap).array(bandList=[62, 116, 39]),
            RasterReader(filename).array(),
        )
