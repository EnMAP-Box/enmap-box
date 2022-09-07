from typing import Dict, List, Union, Tuple

from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp.externals.ee_plugin.provider import BAND_TYPES
from qgis.PyQt.QtGui import QColor
from typeguard import typechecked


@typechecked
class ImageInfo():
    def __init__(self, info: dict):
        self.info = info  # ee.Image.getInfo() of first image in collection
        self.properties: Dict = self.info.get('properties', {})
        self.propertyNames: List[str] = list(sorted(self.properties))
        self.xresolutions = [band['crs_transform'][0] for band in self.info['bands']]
        self.yresolutions = [band['crs_transform'][4] for band in self.info['bands']]
        self.upperLefts = [SpatialPoint(band['crs'], band['crs_transform'][2], band['crs_transform'][5])
                           for band in self.info['bands']]
        self.epsgs = [band['crs'] for band in self.info['bands']]
        self.bandNames = [band['id'] for band in self.info['bands']]
        self.bandCount = len(self.bandNames)
        self.dataTypeRanges = [(band['data_type'].get('min', 0), band['data_type'].get('max', 0)) for band in
                               self.info['bands']]
        self.qgisDataTypes = [BAND_TYPES[band['data_type']['precision']] for band in self.info['bands']]
        self.numpyDataTypes = [Utils.qgisDataTypeToNumpyDataType(dt) for dt in self.qgisDataTypes]
        self.gdalDataTypes = [Utils.qgisDataTypeToGdalDataType(dt) for dt in self.qgisDataTypes]
        self.defaultBandColors = {}
        self.defaultQaFlags = {}
        self.wavebandMapping = {}

    def addDefaultBandColors(self, bandColors: Dict[str, str]):
        for name, color in bandColors.items():
            self.defaultBandColors[name] = QColor(color)

    def addDefaultQaFlags(self, qaFlags: Dict[str, List[Union[str, Tuple[str, str]]]]):
        self.defaultQaFlags.update(qaFlags)

    def addWavebandMappings(self, wavebandMapping: Dict[str, str]):
        self.wavebandMapping.update(wavebandMapping)
