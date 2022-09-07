from enmapbox.exampledata import enmap
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase


class TestRasterProcessing(TestCase):

    def test_multiband_io(self):
        raster = RasterReader(enmap)
        array = raster.array()
        options = ['COMPRESS=LZW', 'INTERLEAVE=BAND']
        outraster = Driver(self.filename('enmap.tif'), options=options).createFromArray(array)
        outraster.setNoDataValue(raster.noDataValue())
        outraster.setMetadata(raster.metadata())

    def test_multiband_io_with_overlap(self):
        raster = RasterReader(enmap)
        overlap = 100
        array = raster.array(overlap=overlap)
        options = ['COMPRESS=LZW', 'INTERLEAVE=BAND']
        outraster = Driver(self.filename('enmap.tif'), options=options).createFromArray(array, overlap=overlap)
        outraster.setNoDataValue(raster.noDataValue())
        outraster.setMetadata(raster.metadata())
        self.assertEqual(array[0].shape,
                         (raster.height() + 2 * overlap, raster.width() + 2 * overlap))
        self.assertEqual(outraster.width(), raster.width())
        self.assertEqual(outraster.height(), raster.height())

    def test_blockwise_multiband_io(self):
        raster = RasterReader(enmap)
        options = ['COMPRESS=LZW', 'INTERLEAVE=BAND']
        outraster = Driver(self.filename('enmap.tif'), options=options).createLike(raster)
        for block in raster.walkGrid(50, 50):
            array = raster.array(block.xOffset, block.yOffset, block.width, block.height)
            outraster.writeArray(array, block.xOffset, block.yOffset)
        outraster.setNoDataValue(raster.noDataValue())
        outraster.setMetadata(raster.metadata())

    def test_blockwise_band_io(self):
        raster = RasterReader(enmap)
        options = ['COMPRESS=LZW', 'INTERLEAVE=BAND']
        outraster = Driver(self.filename('enmap.tif'), options=options).createLike(raster)
        for block in raster.walkGrid(50, 50):
            for bandNo in range(1, raster.bandCount() + 1):
                array = raster.array(block.xOffset, block.yOffset, block.width, block.height, [bandNo])
                outraster.writeArray2d(array[0], bandNo, block.xOffset, block.yOffset)

        outraster.setNoDataValue(raster.noDataValue())
        outraster.setMetadata(raster.metadata())

    def test_nativeBlocks(self):
        raster = RasterReader(enmap)
        blockSizeX, blockSizeY = raster.gdalBand(1).GetBlockSize()
        for block in raster.walkGrid(blockSizeX, blockSizeY):
            pass
