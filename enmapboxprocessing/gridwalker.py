from qgis.PyQt.QtCore import QSize, QSizeF, Qt
from qgis.core import QgsRasterLayer, QgsRasterDataProvider, QgsRectangle, QgsProcessingFeedback

from typeguard import typechecked

from enmapboxprocessing.extentwalker import ExtentWalker


@typechecked
class GridWalker(ExtentWalker):

    def __init__(
            self, extent: QgsRectangle, blockSizeX: int, blockSizeY: int, pixelSizeX: float, pixelSizeY: float,
            feedback: QgsProcessingFeedback = None
    ):
        blockSizeX = float(blockSizeX * pixelSizeX)
        blockSizeY = float(blockSizeY * pixelSizeY)
        super().__init__(extent, blockSizeX, blockSizeY, feedback)
