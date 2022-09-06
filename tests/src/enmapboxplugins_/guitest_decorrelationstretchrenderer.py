from enmapbox.coreapps.decorrelationstretchapp.decorrelationstretchrenderer import DecorrelationStretchRenderer
from qgis.core import QgsRasterLayer
import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.rasterreader import RasterReader
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler, MinMaxScaler

layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
reader = RasterReader(layer)

bandList = [38, 23, 5]

# todo read only a subset of the data
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

percentiles = np.percentile(Xt, [2, 98], axis=0)

scaler2 = MinMaxScaler(feature_range=[0, 255], clip=True)
scaler2.fit(percentiles)
rgb = scaler2.transform(Xt)

renderer = DecorrelationStretchRenderer()
renderer.setTransformer(pca, scaler1, scaler2)
renderer.setBandList(bandList)
layer.setRenderer(renderer)

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
enmapBox._dropObject(layer)

qgsApp.exec_()
