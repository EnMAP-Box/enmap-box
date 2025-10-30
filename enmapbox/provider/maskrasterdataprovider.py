from typing import Optional
from urllib.parse import parse_qsl

import numpy as np

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import QObject
from qgis.core import QgsRasterLayer, QgsRectangle, QgsRasterBlockFeedback, QgsProviderMetadata, QgsProviderRegistry, \
    QgsRasterDataProvider, QgsRasterBlock, Qgis, QgsMessageLog


class MaskRasterDataProvider(QgsRasterDataProvider):
    # ALL_INSTANCES = dict()
    NAME = 'MaskRasterDataProvider'
    DESCRIPTION = 'mask raster data provider'

    P_Uri = 'uri'
    P_Provider = 'provider'
    P_Band = 'band'
    P_MaskNoDataValues = 'maskNoDataValues'
    P_MaskNonFiniteValues = 'maskNonFiniteValues'
    P_MaskValues = 'maskValues'
    P_MaskValueRanges = 'maskValueRanges'
    P_MaskBits = 'maskBits'

    PARENT = QObject()

    # @staticmethod
    # def _release_sip_deleted():
    #     to_delete = {k for k, o in MaskRasterDataProvider.ALL_INSTANCES.items()
    #                  if sip.isdeleted(o)}
    #     for k in to_delete:
    #         MaskRasterDataProvider.ALL_INSTANCES.pop(k)

    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        print(uri)
        assert uri.startswith('?')
        parameters = dict(parse_qsl(uri[1:]))
        self.bandNo = int(parameters.get('band', 1))

        def parseValue(value, default=None):
            if value is None:
                return default
            else:
                return eval(value)

        self.maskNoDataValues = parseValue(parameters.get(self.P_MaskNoDataValues), True)
        self.maskNonFiniteValues = parseValue(parameters.get(self.P_MaskNonFiniteValues), True)
        self.maskValues = parseValue(parameters.get(self.P_MaskValues))
        self.maskValueRanges = parseValue(parameters.get(self.P_MaskValueRanges))
        self.maskBits = parseValue(parameters.get(self.P_MaskBits))
        self.layer = QgsRasterLayer(parameters[self.P_Uri], '', parameters.get(self.P_Provider, 'gdal'))
        assert self.layer.isValid()
        self.provider = self.layer.dataProvider()
        self.reader = RasterReader(self.layer)

    @classmethod
    def createProvider(cls, uri, providerOptions, *args, **kwargs):
        provider = MaskRasterDataProvider(uri)

        # keep a python reference on each new provider instance
        # cls.ALL_INSTANCES[id(provider)] = provider
        # cls._release_sip_deleted()
        provider.setParent(cls.PARENT)
        return provider

    def description(self):
        return self.DESCRIPTION

    def name(self):
        return self.NAME

    def capabilities(self):
        return self.provider.capabilities()

    def transformCoordinates(self, *args, **kwargs):
        return self.provider.transformCoordinates(*args, **kwargs)

    def bandCount(self):
        return 1

    def extent(self):
        return self.provider.extent()

    def crs(self):
        return self.provider.crs()

    def sourceDataType(self, bandNo):
        return Qgis.DataType.Float32

    def dataType(self, bandNo):
        return Qgis.DataType.Float32

    def xSize(self):
        return self.provider.xSize()

    def ySize(self):
        return self.provider.ySize()

    def isValid(self) -> bool:
        return self.provider.isValid()

    def generateBandName(self, bandNumber: int):
        return 'Mask'

    def sample(self, *args, **kwargs):
        raise NotImplementedError()
        return self.provider.sample(*args, **kwargs)

    def identify(self, *args, **kwargs):
        raise NotImplementedError()
        return self.provider.identify(*args, **kwargs)

    def block(
            self, bandNo: int, boundingBox: QgsRectangle, width: int, height: int,
            feedback: QgsRasterBlockFeedback = None
    ) -> Optional[QgsRasterBlock]:

        array = self.reader.arrayFromBoundingBoxAndSize(boundingBox, width, height, bandList=[self.bandNo])[0]
        maskArray = self.reader.maskArray(
            [array], [bandNo], self.maskNonFiniteValues, None, self.maskNoDataValues
        )[0]

        if self.maskValues is not None:
            for value in self.maskValues:
                maskArray[array == value] = False

        if self.maskValueRanges is not None:
            for vmin, vmax in self.maskValueRanges:
                maskArray[np.logical_and(vmin <= array, array <= vmax)] = False

        if self.maskBits is not None:
            for first_bit, bit_count, values in self.maskBits:
                first_bit = int(first_bit)
                bit_count = int(bit_count)
                bitmask = (1 << bit_count) - 1
                arrayShifted = array >> first_bit
                arrayShiftedAndMasked = arrayShifted & bitmask
                for value in values:
                    maskArray[arrayShiftedAndMasked == value] = False

        block = Utils.numpyArrayToQgsRasterBlock(maskArray)
        return block

    def clone(self):
        provider = MaskRasterDataProvider(self.uri)
        return provider


def register_data_provider():
    metadata = QgsProviderMetadata(
        MaskRasterDataProvider.NAME,
        MaskRasterDataProvider.DESCRIPTION,
        MaskRasterDataProvider.createProvider
    )
    registry = QgsProviderRegistry.instance()
    registry.registerProvider(metadata)
    QgsMessageLog.logMessage(f'{MaskRasterDataProvider.NAME} registered', level=Qgis.MessageLevel.Info)
