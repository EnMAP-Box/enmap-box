from typing import NamedTuple

import numpy as np

from qgis.core import QgsRectangle


class RasterBlockInfo(NamedTuple):
    extent: QgsRectangle
    xOffset: int
    yOffset: int
    width: int
    height: int

    def xResolution(self):
        return self.extent.width() / self.width

    def yResolution(self):
        return self.extent.width() / self.width

    def xMap(self):
        xres = self.xResolution()
        ones = np.ones((self.height, 1))
        coordinates = np.arange(
            self.extent.xMinimum() + xres / 2,
            self.extent.xMaximum(),
            xres
        ).reshape(1, -1)
        xmap = ones * coordinates
        return xmap

    def yMap(self):
        yres = self.yResolution()
        ones = np.ones((1, self.width))
        coordinates = np.arange(
            self.extent.yMaximum() - yres / 2,
            self.extent.yMinimum(),
            -yres
        ).reshape(-1, 1)
        ymap = coordinates * ones
        return ymap
