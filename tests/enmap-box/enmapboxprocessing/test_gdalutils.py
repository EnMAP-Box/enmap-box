from osgeo import gdal

from enmapboxprocessing.gdalutils import GdalUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap, enmap_potsdam, enmap_berlin, hires_berlin


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

    def test_stackBands_1raster_3bands(self):
        filename1 = enmap_potsdam
        bandList1 = [48, 30, 16]
        filename = self.filename('stack.vrt')
        GdalUtils.stackBands(filename, [filename1], [bandList1])

        self.assertArrayEqual(
            RasterReader(filename1).array(bandList=bandList1),
            RasterReader(filename).array(),
        )

        self.assertEqual(RasterReader(filename1).bandName(bandList1[0]), RasterReader(filename).bandName(1))
        self.assertEqual(RasterReader(filename1).bandName(bandList1[1]), RasterReader(filename).bandName(2))
        self.assertEqual(RasterReader(filename1).bandName(bandList1[2]), RasterReader(filename).bandName(3))

    def test_stackBands_2raster_4bands_defaultGrid(self):
        filename1 = enmap_berlin
        filename2 = hires_berlin

        bandList1 = [62, 116]
        bandList2 = [3, 2]

        filename = self.filename('stack.vrt')
        GdalUtils.stackBands(filename, [filename1, filename2], [bandList1, bandList2])

        self.assertArrayEqual(
            RasterReader(filename1).array(bandList=bandList1),
            RasterReader(filename).array(bandList=[1, 2]),
        )

    def test_stackBands_2raster_4bands_customGrid(self):
        filename1 = enmap_berlin
        filename2 = hires_berlin

        bandList1 = [62, 116]
        bandList2 = [3, 2]

        filename = self.filename('stack.vrt')
        reader2 = RasterReader(filename2)
        GdalUtils.stackBands(
            filename, [filename1, filename2], [bandList1, bandList2], reader2.width(), reader2.height(),
            reader2.extent()
        )

        self.assertArrayEqual(
            RasterReader(filename2).array(bandList=bandList2),
            RasterReader(filename).array(bandList=[3, 4]),
        )
