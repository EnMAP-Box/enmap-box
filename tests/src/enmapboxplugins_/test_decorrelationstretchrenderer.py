import numpy as np

from decorrelationstretchapp.decorrelationstretchrenderer import DecorrelationStretchRenderer
from qgis.core import QgsRasterLayer, Qgis
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler, MinMaxScaler

from enmapbox.exampledata import enmap
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase
from enmapboxprocessing.utils import Utils


class TestClassFractionRenderer(TestCase):

    def test_enmap(self):
        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)
        bandList = [38, 23, 5]

        # prepare transformers
        array = reader.array(bandList=bandList)
        maskArray = np.all(reader.maskArray(array, bandList), axis=0)
        X = np.transpose([a[maskArray] for a in array])
        pca = PCA(n_components=3)
        pca.fit(X)
        XPca = pca.transform(X)
        quantile_range = (2, 98)
        scaler1 = RobustScaler(with_centering=False, quantile_range=quantile_range)
        scaler1.fit(XPca)
        XPcaStretched = scaler1.transform(XPca)
        Xt = pca.inverse_transform(XPcaStretched)
        percentiles = np.percentile(Xt, quantile_range, axis=0)
        scaler2 = MinMaxScaler(feature_range=[0, 255], clip=True)
        scaler2.fit(percentiles)

        # make renderer
        renderer = DecorrelationStretchRenderer()
        renderer.setTransformer(pca, scaler1, scaler2)
        renderer.setBandList(bandList)
        layer.setRenderer(renderer)

        block = renderer.block(1, layer.extent(), layer.width(), layer.height())
        self.assertEqual(Qgis.ARGB32_Premultiplied, block.dataType())
        self.assertEqual(304813346210224, np.sum(Utils.qgsRasterBlockToNumpyArray(block), dtype=float))
