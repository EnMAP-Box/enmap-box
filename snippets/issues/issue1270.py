from typing import Union

import numpy as np
from qgis.PyQt.QtCore import QObject

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibraryrasterdataprovider import nn_resample
from enmapbox.testing import start_app
from qgis.core import QgsRasterLayer, QgsRasterDataProvider, QgsProviderMetadata, QgsDataProvider, QgsProviderRegistry
from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, Qgis, QgsRasterBlock, QgsApplication, QgsPointXY, \
    QgsRaster, QgsRasterIdentifyResult

qgsApp = QgsApplication.instance()

exec_app = not isinstance(qgsApp, QgsApplication)
if exec_app:
    qgsApp = start_app()


class TestProvider(QgsRasterDataProvider):
    PARENT = QObject()

    @classmethod
    def providerKey(cls) -> str:
        return 'testprovider'

    @classmethod
    def description(self) -> str:
        return 'description'

    @classmethod
    def createProvider(cls, uri, providerOptions, flags=None):
        provider = TestProvider(uri, providerOptions, QgsDataProvider.ReadFlags())
        return provider

    def __init__(self,
                 uri: str,
                 providerOptions: QgsDataProvider.ProviderOptions = QgsDataProvider.ProviderOptions(),
                 flags: Union[QgsDataProvider.ReadFlags, QgsDataProvider.ReadFlag] = QgsDataProvider.ReadFlags(),
                 ):

        self.mOptions = providerOptions
        self.mFlags = flags
        self.mArray = np.array([[[1, 2, 3, 4], [2, 2, 1, 1]], [[2, 3, 4, 5], [2, 3, 2, 3]]]).swapaxes(0, 2)
        super().__init__(uri, providerOptions=providerOptions, flags=flags)

    def wavelength(self, bandNo: int):
        # This is the wavelength function. If a none-GDAL data provider has it,
        # it's wavelength values are assumed to be in Nanometers
        return 42 + bandNo

    def bandCount(self):
        return self.mArray.shape[0]

    def bandScale(self, bandNo: int):
        return 1

    def bandOffset(self, bandNo: int):
        return 0

    def isValid(self):
        return True

    def xSize(self):
        return self.mArray.shape[2]

    def ySize(self):
        return self.mArray.shape[1]

    def sourceDataType(self, bandNo: int):
        return self.dataType(bandNo)

    def sourceHasNoDataValue(self, bandNo):
        return False

    def crs(self):
        return QgsCoordinateReferenceSystem('EPSG:4326')

    def dataType(self, bandNo):
        return Qgis.DataType.Int16

    def htmlMetadata(self):
        return 'Dummy HTML'

    def name(self):
        return 'Dummy name'

    def extent(self):
        return QgsRectangle(0, 0, self.xSize(), self.ySize())

    def clone(self):
        p = TestProvider(self.uri().uri(), self.mOptions, self.mFlags)
        p.setParent(TestProvider.PARENT)
        return p

    def enableProviderResampling(self, enable: bool):
        return False

    def identify(self, point: QgsPointXY, format: QgsRaster.IdentifyFormat,
                 boundingBox: QgsRectangle = ..., width: int = ..., height: int = ...,
                 dpi: int = ...) -> QgsRasterIdentifyResult:

        results = dict()

        x = int(point.x())
        array = self.mArray

        r = None
        if format == QgsRaster.IdentifyFormatValue:

            if 0 <= x < array.shape[-1]:
                for b in range(self.bandCount()):
                    results[b + 1] = float(array[b, 0, x])
        elif format in [QgsRaster.IdentifyFormatHtml, QgsRaster.IdentifyFormatText]:
            results[0] = 'Dummy HTML / Text'

        r = QgsRasterIdentifyResult(format, results)
        return r

    def block(self, bandNo, boundingBox, width, height, feedback=None):
        dt = self.dataType(bandNo)

        block = QgsRasterBlock(dt, width, height)

        mExtent = self.extent()
        if not mExtent.intersects(boundingBox):
            block.setIsNoData()
            return block

        if not mExtent.contains(boundingBox):
            subRect = QgsRasterBlock.subRect(boundingBox, width, height, mExtent)
            block.setIsNoDataExcept(subRect)
        arr = nn_resample(self.mArray, (height, width))
        block.setData(arr.tobytes())
        return block


registry = QgsProviderRegistry.instance()
metadata = QgsProviderMetadata(
    TestProvider.providerKey(),
    TestProvider.description(), TestProvider.createProvider
)
registry.registerProvider(metadata)

layer = QgsRasterLayer('test.tif', 'test', TestProvider.providerKey())
assert isinstance(layer.dataProvider(), TestProvider)

spectralProperties = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)

# TestProvider wavelength is 42 + Band Number
assert spectralProperties.wavelengths() == [43, 44, 45, 46]
assert spectralProperties.wavelengthUnits() == ['Nanometers', 'Nanometers', 'Nanometers', 'Nanometers']

enmapBox = EnMAPBox(load_other_apps=False, load_core_apps=False)
enmapBox.onDataDropped([layer])

if exec_app:
    qgsApp.exec_()
