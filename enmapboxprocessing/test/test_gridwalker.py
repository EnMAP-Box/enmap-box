from enmapboxprocessing.gridwalker import GridWalker
from enmapboxprocessing.test.testcase import TestCase
from qgis.PyQt.QtCore import QSize
from qgis.core import QgsRectangle


class TestExtentWalker(TestCase):

    def test_walkGrid_byLinewise(self):
        size = QSize(3, 2)
        pixelSizeX, pixelSizeY = 30, 30
        extent = QgsRectangle(0, 0, size.width() * pixelSizeX, size.height() * pixelSizeY)
        blockSizeX, blockSizeY = 3, 1
        gridWalker = GridWalker(extent, blockSizeX, blockSizeY, pixelSizeX, pixelSizeY)
        self.assertEqual(gridWalker.nBlocksX(), 1)
        self.assertEqual(gridWalker.nBlocksY(), 2)
        gold = '[<QgsRectangle: 0 30, 90 60>, <QgsRectangle: 0 0, 90 30>]'
        self.assertEqual(str(list(gridWalker)), gold)

    def test_walkExtent_with_blockSize_notMatching_fullExtent(self):
        size = QSize(3, 3)
        pixelSizeX = 30.
        pixelSizeY = 30.
        extent = QgsRectangle(0, 0, size.width() * pixelSizeX, size.height() * pixelSizeY)
        blockSizeX = 2
        blockSizeY = 2
        gridWalker = GridWalker(extent, blockSizeX, blockSizeY, pixelSizeX, pixelSizeY)
        self.assertEqual(gridWalker.nBlocksX(), 2)
        self.assertEqual(gridWalker.nBlocksY(), 2)
        gold = '[<QgsRectangle: 0 30, 60 90>, <QgsRectangle: 60 30, 90 90>, <QgsRectangle: 0 0, 60 30>, <QgsRectangle: 60 0, 90 30>]'
        self.assertEqual(str(list(gridWalker)), gold)
