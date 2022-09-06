from copy import deepcopy
from typing import List

import numpy as np
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
class DecorrelationStretchRenderer(QgsRasterRenderer):
    pca: PCA
    scaler1: RobustScaler
    scaler2: MinMaxScaler
    bandList: List[int]

    def __init__(self, input: QgsRasterInterface = None, type: str = ''):
        super().__init__(input, type)

    def setTransformer(self, pca: PCA, scaler1: RobustScaler, scaler2: MinMaxScaler):
        self.pca = pca
        self.scaler1 = scaler1
        self.scaler2 = scaler2

    def setBandList(self, bandList: List[int]):
        self.bandList = bandList

    def usesBands(self) -> List[int]:
        return list(self.bandList)

    def block(self, band_nr: int, extent: QgsRectangle, width: int, height: int,
              feedback: QgsRasterBlockFeedback = None):
        # read data
        reader = RasterReader(self.input())
        array = reader.array(width=width, height=height, bandList=self.bandList, boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, self.bandList), axis=0)

        # init result
        r = np.zeros((height, width), dtype=np.uint32)
        g = np.zeros((height, width), dtype=np.uint32)
        b = np.zeros((height, width), dtype=np.uint32)
        a = np.zeros((height, width), dtype=np.uint32)

        # convert to sklearn sample format
        X = np.transpose([a[maskArray] for a in array])
        if len(X) > 0:
            # transform data
            XPca = self.pca.transform(X)
            XPcaStretched = self.scaler1.transform(XPca)
            Xt = self.pca.inverse_transform(XPcaStretched)
            XRgb = self.scaler2.transform(Xt)

            # convert back to spatial block
            r[maskArray] = XRgb[:, 0]
            g[maskArray] = XRgb[:, 1]
            b[maskArray] = XRgb[:, 2]

        # mask no data pixel
        a[maskArray] = 255

        # convert back to QGIS raster block
        outarray = (r << 16) + (g << 8) + b + (a << 24)
        return Utils.numpyArrayToQgsRasterBlock(outarray, Qgis.ARGB32_Premultiplied)

    def clone(self) -> QgsRasterRenderer:
        renderer = DecorrelationStretchRenderer()
        renderer.pca = deepcopy(self.pca)
        renderer.scaler1 = deepcopy(self.scaler1)
        renderer.scaler2 = deepcopy(self.scaler2)
        renderer.bandList = deepcopy(self.bandList)
        return renderer
