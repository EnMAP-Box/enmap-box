from typing import List

import numpy as np

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsRasterRenderer, QgsRasterInterface, QgsRectangle, QgsRasterBlockFeedback, Qgis, QgsRasterLayer
from typeguard import typechecked


@typechecked
class MultiSourceMultiBandColorRenderer(QgsRasterRenderer):
    min1: float
    min2: float
    min3: float
    max1: float
    max2: float
    max3: float
    band1: int
    band2: int
    band3: int
    source1: str
    source2: str
    source3: str

    def __init__(self, input: QgsRasterInterface = None, type: str = ''):
        super().__init__(input, type)
        self.min1 = 0.
        self.min2 = 0.
        self.min3 = 0.
        self.max1 = 0.
        self.max2 = 0.
        self.max3 = 0.
        self.band1 = 0
        self.band2 = 0
        self.band3 = 0
        self.source1 = ''
        self.source2 = ''
        self.source3 = ''

    def setRange(
            self, min1: float, min2: float, min3: float, max1: float, max2: float, max3: float
    ):
        self.min1 = min1
        self.min2 = min2
        self.min3 = min3
        self.max1 = max1
        self.max2 = max2
        self.max3 = max3

    def setBands(self, band1: int, band2: int, band3: int):
        self.band1 = band1
        self.band2 = band2
        self.band3 = band3

    def setSources(self, source1: str, source2: str, source3: str):
        self.layer1 = QgsRasterLayer(source1)
        self.layer2 = QgsRasterLayer(source2)
        self.layer3 = QgsRasterLayer(source3)

    def usesBands(self) -> List[int]:
        return []  # potentially, we aren't using any band of the layer itself

    def block(self, band_nr: int, extent: QgsRectangle, width: int, height: int,
              feedback: QgsRasterBlockFeedback = None):
        # read data
        # reader = RasterReader(self.input())

        # init result
        r = np.zeros((height, width), dtype=np.uint32)
        g = np.zeros((height, width), dtype=np.uint32)
        b = np.zeros((height, width), dtype=np.uint32)
        a = np.zeros((height, width), dtype=np.uint32)

        array = list()
        maskArray = list()
        for layer, bandNo in zip([self.layer1, self.layer2, self.layer3], [self.band1, self.band2, self.band3]):
            reader = RasterReader(layer)
            arr = reader.array(width=width, height=height, bandList=[bandNo], boundingBox=extent)
            marr = reader.maskArray(arr, [bandNo])
            array.append(arr[0])
            maskArray.append(marr[0])

        valid = np.all(maskArray, axis=0)

        if valid.sum() != 0:
            valuesR, valuesG, valuesB = [a[valid].astype(float) for a in array]

            # scale
            valuesR = np.clip(255 * (valuesR - self.min1) / (self.max1 - self.min1), 0, 255)
            valuesG = np.clip(255 * (valuesG - self.min2) / (self.max2 - self.min2), 0, 255)
            valuesB = np.clip(255 * (valuesB - self.min3) / (self.max2 - self.min3), 0, 255)

            # convert back to spatial block
            r[valid] = valuesR
            g[valid] = valuesG
            b[valid] = valuesB

            # mask no data pixel
            a[valid] = 255

        # convert back to QGIS raster block
        outarray = (r << 16) + (g << 8) + b + (a << 24)
        return Utils.numpyArrayToQgsRasterBlock(outarray, Qgis.ARGB32_Premultiplied)

    def clone(self) -> QgsRasterRenderer:
        renderer = MultiSourceMultiBandColorRenderer()
        renderer.min1 = self.min1
        renderer.min2 = self.min2
        renderer.min3 = self.min3
        renderer.max1 = self.max1
        renderer.max2 = self.max2
        renderer.max3 = self.max3
        renderer.band1 = self.band1
        renderer.band2 = self.band2
        renderer.band3 = self.band3
        renderer.layer1 = self.layer1.clone()
        renderer.layer2 = self.layer2.clone()
        renderer.layer3 = self.layer3.clone()
        return renderer
