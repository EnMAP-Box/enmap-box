from enmapboxprocessing.gridwalker import GridWalker
from enmapboxprocessing.test.testcase import TestCase
from qgis.PyQt.QtCore import QSize
from qgis.core import QgsRectangle


class TestGridWalker(TestCase):

    def test_walkGrid(self):
        size = QSize(3, 2)
        pixelSizeX, pixelSizeY = 30, 30
        extent = QgsRectangle(0, 0, size.width() * pixelSizeX, size.height() * pixelSizeY)
        blockSizeX, blockSizeY = 3, 1
        gridWalker = GridWalker(extent, blockSizeX, blockSizeY, pixelSizeX, pixelSizeY)
        self.assertEqual(gridWalker.nBlocksX(), 1)
        self.assertEqual(gridWalker.nBlocksY(), 2)
