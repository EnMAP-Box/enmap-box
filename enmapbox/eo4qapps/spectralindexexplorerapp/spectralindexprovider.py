import json
import traceback
from os.path import join, dirname
from typing import Optional

import numpy as np
from qgis.PyQt import sip
from qgis.core import QgsRasterLayer, QgsRectangle, QgsRasterBlockFeedback, QgsProviderMetadata, QgsProviderRegistry, \
    QgsRasterDataProvider, QgsRasterBlock, Qgis, QgsMessageLog

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils


class SpectralIndexRasterDataProvider(QgsRasterDataProvider):
    ALL_INSTANCES = dict()
    NAME = 'SpectralIndexRasterDataProvider'
    DESCRIPTION = 'spectral index raster data provider'
    BANDS = Utils.jsonLoad(join(dirname(__file__), 'spyndex/data/bands.json'))
    CONSTANTS = Utils.jsonLoad(join(dirname(__file__), 'spyndex/data/constants.json'))
    INDIZES = Utils.jsonLoad(join(dirname(__file__), 'spyndex/data/spectral-indices-dict.json'))

    @staticmethod
    def _release_sip_deleted():
        to_delete = {k for k, o in SpectralIndexRasterDataProvider.ALL_INSTANCES.items()
                     if sip.isdeleted(o)}
        for k in to_delete:
            SpectralIndexRasterDataProvider.ALL_INSTANCES.pop(k)

    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        layerUri, meta = uri.split('?')
        meta = json.loads(meta)
        assert isinstance(meta, dict)
        assert 'indices' in meta
        if not isinstance(meta['indices'], list):
            raise NotImplementedError()
        self.meta = meta
        self.layer = QgsRasterLayer(layerUri)
        self.provider = self.layer.dataProvider()
        self.reader = RasterReader(self.layer)

    @classmethod
    def createProvider(cls, uri, providerOptions, *args, **kwargs):
        provider = SpectralIndexRasterDataProvider(uri)

        # keep a python reference on each new provider instance
        cls.ALL_INSTANCES[id(provider)] = provider
        cls._release_sip_deleted()
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
        return len(self.meta['indices'])

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
        return self.meta['indices'][bandNumber - 1]['short_name']

    def sample(self, *args, **kwargs):
        return self.provider.sample(*args, **kwargs)

    def identify(self, *args, **kwargs):
        return self.provider.identify(*args, **kwargs)

    def block(
            self, bandNo: int, boundingBox: QgsRectangle, width: int, height: int,
            feedback: QgsRasterBlockFeedback = None
    ) -> Optional[QgsRasterBlock]:

        try:
            spec = self.meta['indices'][bandNo - 1]
            keys = spec['bands']
            formula = spec['formula']
            values = dict()
            for key in keys:
                if key in self.CONSTANTS:
                    value = self.meta['band_mapping'].get(key, self.CONSTANTS[key])
                elif key in self.BANDS:
                    sourceBandNo = self.meta['band_mapping'][key]
                    value = np.array(
                        self.reader.arrayFromBoundingBoxAndSize(boundingBox, width, height, bandList=[sourceBandNo])[0],
                        dtype=np.float32
                    )
                values[key] = value
            array = eval(formula, values)
        except Exception:
            traceback.print_exc()
            array = None

        block = Utils.numpyArrayToQgsRasterBlock(array)
        return block

    def clone(self):
        provider = SpectralIndexRasterDataProvider(self.uri)
        return provider


def register_data_provider():
    metadata = QgsProviderMetadata(
        SpectralIndexRasterDataProvider.NAME,
        SpectralIndexRasterDataProvider.DESCRIPTION,
        SpectralIndexRasterDataProvider.createProvider
    )
    registry = QgsProviderRegistry.instance()
    registry.registerProvider(metadata)
    QgsMessageLog.logMessage(f'{SpectralIndexRasterDataProvider.NAME} registered', level=Qgis.MessageLevel.Info)
