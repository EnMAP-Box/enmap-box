from enmapboxprocessing.extentwalker import ExtentWalker
from enmapboxprocessing.test.testcase import TestCase
from qgis.core import QgsProcessingFeedback, QgsRectangle


class TestExtentWalker(TestCase):

    def test(self):
        sizex = 4
        sizey = 6
        extent = QgsRectangle(0, 0, sizex, sizey)
        blockSizeX, blockSizeY = 4, 5
        extentWalker = ExtentWalker(extent, blockSizeX, blockSizeY, QgsProcessingFeedback())
        self.assertEqual(1, extentWalker.nBlocksX())
        self.assertEqual(2, extentWalker.nBlocksY())
        self.assertListEqual([QgsRectangle(0, 1, 4, 6), QgsRectangle(0, 0, 4, 1)], list(extentWalker))
