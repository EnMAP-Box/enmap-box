from enmapboxprocessing.extentwalker import ExtentWalker
from enmapboxprocessing.test.testcase import TestCase
from qgis.core import QgsRectangle


class TestExtentWalker(TestCase):

    def test_walkExtent_with_2x3_blocks_ofSize_4x5(self):
        nx = 2
        ny = 3
        sizex = 4
        sizey = 5
        extent = QgsRectangle(0, 0, nx * sizex, ny * sizey)
        blockSizeX, blockSizeY = 4, 5
        extentWalker = ExtentWalker(extent, blockSizeX, blockSizeY)
        self.assertEqual(extentWalker.nBlocksX(), nx)
        self.assertEqual(extentWalker.nBlocksY(), ny)

    def test_walkExtent_with_blockSize_thatDoesNotMatch(self):
        extent = QgsRectangle(0, 0, 3, 3)
        blockSizeX, blockSizeY = 4, 5
        for blockExtent in ExtentWalker(extent, blockSizeX, blockSizeY):
            print(blockExtent.width(), blockExtent.height())
