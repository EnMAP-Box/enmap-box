from copy import deepcopy
from typing import List, Optional, Tuple

import numpy as np

from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRasterRenderer, QgsRasterInterface, QgsRectangle, QgsRasterBlockFeedback, QgsRasterBlock, \
    Qgis
from typeguard import typechecked


@typechecked
class EnhancedMultiBandColorRenderer(QgsRasterRenderer):
    colors: Optional[List[QColor]]
    minMaxValues: Optional[List[Tuple[float, float]]]

    def __init__(self, input: QgsRasterInterface, type: str = ''):
        super().__init__(input, type)
        self.colors = None
        self.minMaxValues = None

    def setColors(self, colors: List[QColor]):
        if len(colors) != self.input().bandCount():
            raise ValueError('number of colors must match number of bands.')
        self.colors = colors

    def setMinMaxValues(self, minMaxValues: List[Tuple[float, float]]):
        if len(minMaxValues) != self.input().bandCount():
            raise ValueError('number of min-max values must match number of bands.')
        self.minMaxValues = minMaxValues

    def isValid(self) -> bool:
        if self.colors is None:
            return False
        if self.minMaxValues is None:
            return False
        return True

    def block(self, band_nr: int, extent: QgsRectangle, width: int, height: int,
              feedback: QgsRasterBlockFeedback = None):

        r = np.zeros((height, width), dtype=np.float32)
        g = np.zeros((height, width), dtype=np.float32)
        b = np.zeros((height, width), dtype=np.float32)
        a = np.zeros((height, width), dtype=np.float32)

        if self.isValid():
            # Sum up band-wise RGB values.
            usedBandCount = 0

            arraySum = np.zeros((height, width), dtype=np.float32)
            rSum = np.zeros((height, width), dtype=np.float32)
            gSum = np.zeros((height, width), dtype=np.float32)
            bSum = np.zeros((height, width), dtype=np.float32)

            for bandNo, (color, (vmin, vmax)) in enumerate(zip(self.colors, self.minMaxValues), 1):
                print(vmin, vmax, 'ORIG')
                if color.alpha() == 0:
                    continue
                usedBandCount += 1

                # read raw data
                block: QgsRasterBlock = self.input().block(bandNo, extent, width, height)
                array = Utils.qgsRasterBlockToNumpyArray(block).astype(np.float32)

                # scale to 0-1 range and clip tails
                array -= vmin
                array /= (vmax - vmin)
                np.clip(array, 0, 1, out=array)

                # print(color.redF(), color.greenF(), color.blueF())

                r += color.red() * array
                g += color.green() * array
                b += color.blue() * array
                a[array > 0] = 255  # every used pixel gets full opacity

                arraySum += array
                rSum += color.redF()
                gSum += color.greenF()
                bSum += color.blueF()

            if 0:
                # scale to 0-255 range
                if usedBandCount > 0:
                    r /= rSum
                    g /= gSum
                    b /= bSum

            if 1:
                # scale to 0-255 range
                if usedBandCount > 0:
                    r /= usedBandCount
                    g /= usedBandCount
                    b /= usedBandCount

                if 1:
                    # enhance contrast
                    values = np.array([r, g, b])
                    values = values[np.isfinite(values)]
                    vmin, vmax = np.percentile(values, [2, 98])
                    # vmin, vmax = np.percentile(r, [2, 98])
                    r -= vmin
                    r /= (vmax - vmin) / 255
                    print(vmin, vmax, r.min(), r.max())
                    # vmin, vmax = np.percentile(g, [2, 98])
                    g -= vmin
                    g /= (vmax - vmin) / 255
                    # vmin, vmax = np.percentile(b, [2, 98])
                    b -= vmin
                    b /= (vmax - vmin) / 255

        # clip RGBs to 0-255, to ensure float values aren't slightly off
        np.clip(r, 0, 255, r)
        np.clip(g, 0, 255, g)
        np.clip(b, 0, 255, b)

        # convert back to QGIS raster block
        rgba = np.array([r, g, b, a], dtype=np.uint32)
        outarray = (rgba[0] << 16) + (rgba[1] << 8) + rgba[2] + (rgba[3] << 24)
        return Utils.numpyArrayToQgsRasterBlock(outarray, Qgis.ARGB32_Premultiplied)

    def clone(self) -> QgsRasterRenderer:
        renderer = EnhancedMultiBandColorRenderer(self.input())
        renderer.colors = deepcopy(self.colors)
        renderer.minMaxValues = deepcopy(self.minMaxValues)
        return renderer
