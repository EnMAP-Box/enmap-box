from typing import List

import numpy as np

from qgis.core import QgsRasterRenderer, QgsRasterInterface, QgsRectangle, QgsRasterBlockFeedback, Qgis

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from typeguard import typechecked


@typechecked
class CmykColorRasterRenderer(QgsRasterRenderer):
    min1: float
    min2: float
    min3: float
    min4: float
    max1: float
    max2: float
    max3: float
    max4: float

    band1: int
    band2: int
    band3: int
    band4: int

    def __init__(self, input: QgsRasterInterface = None, type: str = ''):
        super().__init__(input, type)
        self.min1 = 0.
        self.min2 = 0.
        self.min3 = 0.
        self.min4 = 0.
        self.max1 = 0.
        self.max2 = 0.
        self.max3 = 0.
        self.max4 = 0.
        self.band1 = 0
        self.band2 = 0
        self.band3 = 0
        self.band4 = 0

    def setRange(
            self, min1: float, min2: float, min3: float, min4: float, max1: float, max2: float, max3: float, max4: float
    ):
        self.min1 = min1
        self.min2 = min2
        self.min3 = min3
        self.min4 = min4
        self.max1 = max1
        self.max2 = max2
        self.max3 = max3
        self.max4 = max4

    def setBands(self, band1: int, band2: int, band3: int, band4: int):
        self.band1 = band1
        self.band2 = band2
        self.band3 = band3
        self.band4 = band4

    def usesBands(self) -> List[int]:
        return [self.band1, self.band2, self.band3, self.band4]

    def block(self, band_nr: int, extent: QgsRectangle, width: int, height: int,
              feedback: QgsRasterBlockFeedback = None):
        # read data
        reader = RasterReader(self.input())
        bandList = [self.band1, self.band2, self.band3, self.band4]
        array = reader.array(width=width, height=height, bandList=bandList, boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, bandList), axis=0)
        array1, array2, array3, array4 = array
        values1 = array1[maskArray]
        values2 = array2[maskArray]
        values3 = array3[maskArray]
        values4 = array4[maskArray]

        if len(values1) == 0:
            return

        # init result
        r = np.zeros((height, width), dtype=np.uint32)
        g = np.zeros((height, width), dtype=np.uint32)
        b = np.zeros((height, width), dtype=np.uint32)
        a = np.zeros((height, width), dtype=np.uint32)

        # convert CMYK to RGB
        valuesC = (values1 - self.min1) / (self.max1 - self.min1)
        valuesM = (values2 - self.min2) / (self.max2 - self.min2)
        valuesY = (values3 - self.min3) / (self.max2 - self.min3)
        valuesK = (values4 - self.min4) / (self.max2 - self.min4)
        valuesR = np.clip(255 * (1.0 - valuesC) * (1.0 - valuesK), 0, 255)
        valuesG = np.clip(255 * (1.0 - valuesM) * (1.0 - valuesK), 0, 255)
        valuesB = np.clip(255 * (1.0 - valuesY) * (1.0 - valuesK), 0, 255)

        # convert back to spatial block
        r[maskArray] = valuesR
        g[maskArray] = valuesG
        b[maskArray] = valuesB

        # mask no data pixel
        a[maskArray] = 255

        # convert back to QGIS raster block
        outarray = (r << 16) + (g << 8) + b + (a << 24)
        return Utils.numpyArrayToQgsRasterBlock(outarray, Qgis.ARGB32_Premultiplied)

    def clone(self) -> QgsRasterRenderer:
        renderer = CmykColorRasterRenderer()
        renderer.min1 = self.min1
        renderer.min2 = self.min2
        renderer.min3 = self.min3
        renderer.min4 = self.min4
        renderer.max1 = self.max1
        renderer.max2 = self.max2
        renderer.max3 = self.max3
        renderer.max4 = self.max4
        renderer.band1 = self.band1
        renderer.band2 = self.band2
        renderer.band3 = self.band3
        renderer.band4 = self.band4
        return renderer
