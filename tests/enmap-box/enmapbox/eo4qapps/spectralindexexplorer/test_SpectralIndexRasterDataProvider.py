import json

from qgis.core import QgsRasterLayer

from enmapbox import initAll
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from spectralindexexplorerapp.spectralindexprovider import SpectralIndexRasterDataProvider

initAll()


class TestSpectralIndexRasterDataProvider(TestCase):

    def test_singleCustom_withMapping(self):
        meta = {
            'indices': [
                {
                    'short_name': 'MyEVI',
                    'formula': 'g * (N - R) / (N + C1 * R - C2 * B + L)',
                    'bands': ['g', 'N', 'R', 'C1', 'C2', 'B', 'L'],
                    'long_name': 'Enhanced Vegetation Index',
                    'reference': 'https://doi.org/10.1016/S0034-4257(96)00112-5'
                }
            ],
            'band_mapping': {'B': 16, 'R': 48, 'N': 71, 'g': 2.5, 'C1': 6, 'C2': 7.5, 'L': 1}
        }
        uri = f'{enmap}?{json.dumps(meta)}'
        layer = QgsRasterLayer(uri, 'MyEVI', SpectralIndexRasterDataProvider.NAME)
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.dataProvider().name(), SpectralIndexRasterDataProvider.NAME)
        self.assertEqual(layer.bandName(1), 'MyEVI')
        block = layer.dataProvider().block(1, layer.extent(), layer.width(), layer.height())
        assert (block.width(), block.height()) == (220, 400)
        self.assertEqual(round(block.value(100, 100), 2), 0.19)

        reader = RasterReader(layer, openWithGdal=False)
        array = reader.array()[0]
        self.assertEqual(round(float(array[100, 100]), 2), 0.19)
        a = 1
