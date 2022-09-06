from copy import deepcopy
from typing import List, Optional

import numpy as np
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRasterRenderer, QgsRasterInterface, QgsRectangle, QgsRasterBlockFeedback, QgsRasterBlock, \
    Qgis

from enmapboxprocessing.utils import Utils
from typeguard import typechecked


@typechecked
class ClassFractionRenderer(QgsRasterRenderer):

    def __init__(self, input: QgsRasterInterface, type: str = ''):
        super().__init__(input, type)
        self.colors: Optional[List[QColor]] = None

    def setColors(self, colors: List[Optional[QColor]]):
        if len(colors) != self.input().bandCount():
            raise ValueError('number of colors must match number of bands.')
        self.colors = colors

    def usesBands(self) -> List[int]:
        return [bandNo for bandNo in range(1, self.input().bandCount() + 1)]

    def block(self, band_nr: int, extent: QgsRectangle, width: int, height: int,
              feedback: QgsRasterBlockFeedback = None):

        # Sum up weighted category RGBs.
        # We assume weights to be between 0 and 1.
        # We assume that the sum of all weights for a single pixel is <=1.

        r = np.zeros((height, width), dtype=np.float32)
        g = np.zeros((height, width), dtype=np.float32)
        b = np.zeros((height, width), dtype=np.float32)
        a = np.zeros((height, width), dtype=np.float32)

        if self.colors is not None:
            for bandNo, color in enumerate(self.colors, 1):
                if color.alpha() == 0:
                    continue

                block: QgsRasterBlock = self.input().block(bandNo, extent, width, height)
                weight = Utils.qgsRasterBlockToNumpyArray(block)
                if block.hasNoDataValue():
                    weight[weight == block.noDataValue()] = 0
                r += color.red() * weight
                g += color.green() * weight
                b += color.blue() * weight
                a[weight > 0] = 255   # every used pixel gets full opacity

        # clip RGBs to 0-255, in case the assumptions where violated
        np.clip(r, 0, 255, r)
        np.clip(g, 0, 255, g)
        np.clip(b, 0, 255, b)

        # convert back to QGIS raster block
        rgba = np.array([r, g, b, a], dtype=np.uint32)
        outarray = (rgba[0] << 16) + (rgba[1] << 8) + rgba[2] + (rgba[3] << 24)
        return Utils.numpyArrayToQgsRasterBlock(outarray, Qgis.ARGB32_Premultiplied)

    def clone(self) -> QgsRasterRenderer:
        renderer = ClassFractionRenderer(self.input())
        renderer.colors = deepcopy(self.colors)
        return renderer
