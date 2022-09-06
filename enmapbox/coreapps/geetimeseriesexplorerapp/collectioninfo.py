from math import inf, nan
from typing import Dict, List, Tuple

from qgis.PyQt.QtCore import QDate, QDateTime

from typeguard import typechecked


@typechecked
class CollectionInfo():
    def __init__(self, data: dict):
        self.data = data

    def id(self) -> str:
        return self.data['id']

    def googleEarthEngineUrl(self):
        for provider in self.data['providers']:
            if provider['name'] == "Google Earth Engine":
                return provider['url']
        assert 0, 'missing Google Earth Engine url'

    def eo_band(self, bandNo: int) -> Dict:
        if bandNo <= len(self.data['summaries']['eo:bands']):
            return self.data['summaries']['eo:bands'][bandNo - 1]
        return {}  # handle derived vegetation indices silently

    def groundSamplingDistance(self) -> float:
        if 'gsd' in self.data['summaries']:
            return float(min(self.data['summaries']['gsd']))
        gsd = inf
        for eoBand in self.data['summaries']['eo:bands']:
            gsd = min(gsd, eoBand['gsd'])
        return gsd

    def visualizations(self) -> List[Dict]:
        return self.data['summaries']['gee:visualizations']

    def bandWavelength(self, bandNo: int) -> float:
        eoBand = self.eo_band(bandNo)
        if 'center_wavelength' in eoBand:
            wavelength = eoBand['center_wavelength']  # always Micrometers?
            wavelength *= 1000.
            if wavelength > 3000:  # skip thermal bands
                wavelength = nan
        else:
            wavelength = nan
        return wavelength

    def isBitmaskBand(self, bandNo: int) -> bool:
        return 'gee:bitmask' in self.eo_band(bandNo)

    def isClassificationBand(self, bandNo: int) -> bool:
        return 'gee:classes' in self.eo_band(bandNo)

    def bandDescription(self, bandNo: int) -> str:
        return self.eo_band(bandNo).get('description', 'No description available.')

    def bandTooltip(self, bandNo: int) -> str:
        eo_band = self.eo_band(bandNo)
        tooltip = self.bandDescription(bandNo)
        if 'gee:wavelength' in eo_band:
            tooltip += ' [' + eo_band['gee:wavelength'].replace('&mu;m', 'µm') + ']'
        return tooltip

    def bandOffset(self, bandNo: int) -> float:
        return self.eo_band(bandNo).get('gee:offset', 0.)

    def bandScale(self, bandNo: int) -> float:
        return self.eo_band(bandNo).get('gee:scale', 1.)

    def temporalInterval(self) -> Tuple[QDate, QDate]:
        timestamp1, timestamp2 = self.data['extent']['temporal']['interval'][0]

        if timestamp1 is None:
            d1 = QDate(1970, 1, 1)
        else:
            d1 = QDate(*map(int, timestamp1.split('T')[0].split('-')))

        if timestamp2 is None:
            d2 = QDateTime.currentDateTime().date()
        else:
            d2 = QDate(*map(int, timestamp2.split('T')[0].split('-')))
        return d1, d2
