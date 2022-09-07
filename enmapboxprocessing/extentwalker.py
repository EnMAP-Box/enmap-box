import math

from qgis.core import QgsRectangle, QgsProcessingFeedback, QgsProcessingException
from typeguard import typechecked


@typechecked
class ExtentWalker(object):

    def __init__(
            self, extent: QgsRectangle, blockSizeX: float, blockSizeY: float, feedback: QgsProcessingFeedback = None
    ):
        self.extent = extent
        self.blockSizeX = blockSizeX
        self.blockSizeY = blockSizeY
        self.feedback = feedback

    def __iter__(self):
        n = self.nBlocksX() * self.nBlocksY()
        i = 1
        for y in range(self.nBlocksY()):
            for x in range(self.nBlocksX()):
                if self.feedback is not None:
                    self.feedback.setProgress(i / n * 100)
                    if self.feedback.isCanceled():
                        raise QgsProcessingException()
                i += 1
                left = self.extent.xMinimum() + x * self.blockSizeX
                top = self.extent.yMaximum() - y * self.blockSizeY
                right = left + self.blockSizeX
                bottom = top - self.blockSizeY
                blockExtent = QgsRectangle(left, bottom, right, top).intersect(self.extent)
                yield blockExtent

    def nBlocksX(self) -> int:
        return math.ceil(self.extent.width() / self.blockSizeX)

    def nBlocksY(self) -> int:
        return math.ceil(self.extent.height() / self.blockSizeY)
