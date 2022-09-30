from typing import List

import numpy as np
from scipy.stats import binned_statistic_2d

from qgis.core import QgsRasterRenderer, QgsRasterInterface, QgsRectangle, QgsRasterBlockFeedback, Qgis

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import RobustScaler, MinMaxScaler
except ModuleNotFoundError:
    from unittest.mock import Mock

    RobustScaler = MinMaxScaler = PCA = Mock()

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from typeguard import typechecked


@typechecked
class BivariateColorRasterRenderer(QgsRasterRenderer):
    min1: float
    min2: float
    max1: float
    max2: float

    band1: int
    band2: int
    colorPlane: np.ndarray

    def __init__(self, input: QgsRasterInterface = None, type: str = ''):
        super().__init__(input, type)
        self.min1 = 0.
        self.min2 = 0.
        self.max1 = 0.
        self.max2 = 0.
        self.band1 = 0
        self.band2 = 0
        self.colorPlane = np.zeros((256, 256, 3))

    def setColorPlane(self, colorPlane: np.ndarray):
        assert colorPlane.ndim == 3
        assert colorPlane.shape[0] == colorPlane.shape[1], 'color plane must be squared'
        assert colorPlane.shape[2] == 3
        self.colorPlane = colorPlane

    def setRange(self, min1: float, min2: float, max1: float, max2: float):
        self.min1 = min1
        self.min2 = min2
        self.max1 = max1
        self.max2 = max2

    def setBinEdges(self, binEdges1: np.ndarray, binEdges2: np.ndarray):
        self.binEdges1 = binEdges1
        self.binEdges2 = binEdges2

    def setBands(self, band1: int, band2: int):
        self.band1 = band1
        self.band2 = band2

    def usesBands(self) -> List[int]:
        return [self.band1, self.band2]

    def block(self, band_nr: int, extent: QgsRectangle, width: int, height: int,
              feedback: QgsRasterBlockFeedback = None):
        # read data
        reader = RasterReader(self.input())
        array = reader.array(width=width, height=height, bandList=[self.band1, self.band2], boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, [self.band1, self.band2]), axis=0)
        array1, array2 = array
        values1 = array1[maskArray]
        values2 = array2[maskArray]

        if len(values1) == 0:
            return

        # init result
        r = np.zeros((height, width), dtype=np.uint32)
        g = np.zeros((height, width), dtype=np.uint32)
        b = np.zeros((height, width), dtype=np.uint32)
        a = np.zeros((height, width), dtype=np.uint32)

        # find bin colors
        bins = self.colorPlane.shape[0]
        counts, x_edge, y_edge, binnumber = binned_statistic_2d(
            values1, values2, values1, 'count', [self.binEdges1, self.binEdges2], None, True
        )

        binnumber = np.minimum(binnumber, bins - 1)  # need to trim, seams to be a bug in binned_statistic_2d
        colors = self.colorPlane[bins - binnumber[1] - 1, binnumber[0]]

        # convert back to spatial block
        r[maskArray] = colors[:, 0]
        g[maskArray] = colors[:, 1]
        b[maskArray] = colors[:, 2]

        # mask no data pixel
        a[maskArray] = 255

        # convert back to QGIS raster block
        outarray = (r << 16) + (g << 8) + b + (a << 24)
        return Utils.numpyArrayToQgsRasterBlock(outarray, Qgis.ARGB32_Premultiplied)

    def clone(self) -> QgsRasterRenderer:
        renderer = BivariateColorRasterRenderer()
        renderer.min1 = self.min1
        renderer.min2 = self.min2
        renderer.max1 = self.max1
        renderer.max2 = self.max2
        renderer.band1 = self.band1
        renderer.band2 = self.band2
        renderer.colorPlane = self.colorPlane.copy()
        renderer.binEdges1 = self.binEdges1.copy()
        renderer.binEdges2 = self.binEdges2.copy()

        return renderer
