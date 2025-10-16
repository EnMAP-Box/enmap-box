from math import nan, inf
from urllib.parse import urlencode

import numpy as np
from qgis.core import QgsRasterLayer

from enmapbox import initAll
from enmapbox.provider.maskrasterdataprovider import MaskRasterDataProvider
from enmapbox.testing import start_app
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase

start_app()
initAll()


class TestMaskRasterDataProvider(TestCase):

    def test_default(self):
        # default masks nan, inf and nodata
        p = MaskRasterDataProvider
        writer = self.rasterFromArray([[[nan, np.nan, inf, np.inf, -99]]])
        writer.setNoDataValue(-99, 1)
        writer.close()

        parameters = {
            p.P_Uri: writer.source()
        }
        uri = '?' + urlencode(parameters)
        print(uri)
        layer = QgsRasterLayer(uri, 'mask', p.NAME)

        assert layer.isValid()
        reader = RasterReader(layer)
        array = reader.array()
        self.assertListEqual([0, 0, 0, 0, 0], array[0][0].tolist())

    def test_maskNothing(self):
        p = MaskRasterDataProvider
        writer = self.rasterFromArray([[[nan, np.nan, inf, np.inf, -99]]])
        writer.setNoDataValue(-99, 1)
        writer.close()

        parameters = {
            p.P_Uri: writer.source(),
            p.P_MaskNoDataValues: False,
            p.P_MaskNonFiniteValues: False
        }
        uri = '?' + urlencode(parameters)
        layer = QgsRasterLayer(uri, 'mask', p.NAME)

        assert layer.isValid()
        reader = RasterReader(layer)
        array = reader.array()
        self.assertListEqual([1, 1, 1, 1, 1], array[0][0].tolist())

    def test_values(self):
        p = MaskRasterDataProvider
        writer = self.rasterFromArray([[[0, 1, 2, 3]]])
        writer.close()

        parameters = {
            p.P_Uri: writer.source(),
            p.P_MaskValues: [1, 2]
        }
        uri = '?' + urlencode(parameters)
        layer = QgsRasterLayer(uri, 'mask', p.NAME)

        assert layer.isValid()
        reader = RasterReader(layer)
        array = reader.array()
        self.assertListEqual([1, 0, 0, 1], array[0][0].tolist())

    def test_value_ranges(self):
        p = MaskRasterDataProvider
        writer = self.rasterFromArray([[[0, 1, 2, 3]]])
        writer.close()

        parameters = {
            p.P_Uri: writer.source(),
            p.P_MaskValueRanges: [(-10, -5), (-1, 0), (3, 10)]
        }
        uri = '?' + urlencode(parameters)
        layer = QgsRasterLayer(uri, 'mask', p.NAME)

        assert layer.isValid()
        reader = RasterReader(layer)
        array = reader.array()
        self.assertListEqual([0, 1, 1, 0], array[0][0].tolist())

    def test_bitMask(self):
        p = MaskRasterDataProvider
        writer = self.rasterFromArray([[[
            0b000, 0b001,  # matches 0
            0b100, 0b010, 0b011, 0b101,
            0b110, 0b111  # matches 3
        ]]])
        writer.close()

        first_bit = 1
        bit_count = 2
        value1 = 0
        value2 = 3

        parameters = {
            p.P_Uri: writer.source(),
            p.P_MaskBits: [(first_bit, bit_count, (value1, value2))]
        }
        uri = '?' + urlencode(parameters)
        layer = QgsRasterLayer(uri, 'mask', p.NAME)

        assert layer.isValid()
        reader = RasterReader(layer)
        array = reader.array()
        self.assertListEqual([0, 0, 1, 1, 1, 1, 0, 0], array[0][0].tolist())
