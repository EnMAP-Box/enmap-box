from math import nan, inf

import numpy as np

from enmapboxprocessing.algorithm.createmaskalgorithm import CreateMaskAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestCreateMaskAlgorithm(TestCase):

    def test_nonFinite_and_noData(self):
        writer = self.rasterFromArray([[[nan, np.nan, inf, np.inf, -99]]])
        writer.setNoDataValue(-99, 1)
        writer.close()

        alg = CreateMaskAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_BAND: 1,
            alg.P_MASK_NO_DATA_VALUES: True,
            alg.P_MASK_NONFINITE_VALUES: True,
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertListEqual([0, 0, 0, 0, 0], RasterReader(result[alg.P_OUTPUT_MASK]).array()[0][0].tolist())

        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_BAND: 1,
            alg.P_MASK_NO_DATA_VALUES: False,
            alg.P_MASK_NONFINITE_VALUES: False,
            alg.P_OUTPUT_MASK: self.filename('mask2.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertListEqual([1, 1, 1, 1, 1], RasterReader(result[alg.P_OUTPUT_MASK]).array()[0][0].tolist())

    def test_values(self):
        writer = self.rasterFromArray([[[0, 1, 2, 3]]])
        writer.close()

        alg = CreateMaskAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_BAND: 1,
            alg.P_MASK_VALUES: ['1', '2'],
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertListEqual([1, 0, 0, 1], RasterReader(result[alg.P_OUTPUT_MASK]).array()[0][0].tolist()
                             )

    def test_value_ranges(self):
        writer = self.rasterFromArray([[[0, 1, 2, 3]]])
        writer.close()

        alg = CreateMaskAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_BAND: 1,
            alg.P_MASK_VALUE_RANGES: ['-10', '-5',
                                      '-1', '0',
                                      '3', '10'],
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertListEqual([0, 1, 1, 0], RasterReader(result[alg.P_OUTPUT_MASK]).array()[0][0].tolist())

    def test_bitMask(self):
        writer = self.rasterFromArray([[[
            0b000, 0b001,  # matches 0
            0b100, 0b010, 0b011, 0b101,
            0b110, 0b111  # matches 3
        ]]])
        writer.close()

        first_bit = '1'
        bit_count = '2'
        values1 = '0'
        values2 = '3'

        alg = CreateMaskAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_BAND: 1,
            alg.P_MASK_BITS: [first_bit, bit_count, values1,
                              first_bit, bit_count, values2],
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertListEqual([0, 0, 1, 1, 1, 1, 0, 0], RasterReader(result[alg.P_OUTPUT_MASK]).array()[0][0].tolist())
