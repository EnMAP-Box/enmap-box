from enmapboxprocessing.extentwalker import ExtentWalker
from qgis.core import QgsRectangle, QgsProcessingFeedback
from typeguard import typechecked


@typechecked
class GridWalker(ExtentWalker):

    def __init__(
            self, extent: QgsRectangle, blockSizeX: int, blockSizeY: int, pixelSizeX: float, pixelSizeY: float,
            feedback: QgsProcessingFeedback = None
    ):
        blockSizeX = float(blockSizeX * pixelSizeX)
        blockSizeY = float(blockSizeY * pixelSizeY)
        super().__init__(extent, blockSizeX, blockSizeY, feedback)
