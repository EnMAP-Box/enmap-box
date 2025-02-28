import numpy as np

from enmapboxprocessing.algorithm.preparerasteralgorithm import PrepareRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import hires_berlin
from qgis.core import Qgis


class TestPrepareRasterAlgorithm(TestCase):

    def test_doNothing(self):
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: hires_berlin,
            alg.P_OUTPUT_RASTER: self.filename('raster3.tif'),
        }
        self.runalg(alg, parameters)
        reader1 = RasterReader(hires_berlin)
        reader2 = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array1 = reader1.array()
        array2 = reader2.array()
        self.assertArrayEqual(array1, array2)
        self.assertEqual(array1[0].dtype, array2[0].dtype)

    def test_offset(self):
        writer = self.rasterFromValue((1, 1, 1), 10, 'inraster.tif')
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_OFFSET: 3,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertArrayEqual(13, array)

    def test_scale(self):
        writer = self.rasterFromValue((1, 1, 1), 10, 'inraster.tif')
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_SCALE: 2,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertArrayEqual(20, array)

    def test_scaleBandWise(self):
        writer = self.rasterFromValue((2, 1, 1), 10, 'inraster.tif')
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_SCALE: [2, 3],
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertArrayEqual(np.array([20, 30]), np.array(array).flatten())

    def test_type(self):
        writer = self.rasterFromValue((1, 1, 1), 10, 'inraster.tif')
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_DATA_TYPE: alg.Float32,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        self.assertEqual(Qgis.DataType.Float32, RasterReader(parameters[alg.P_OUTPUT_RASTER]).dataType())

    def test_min(self):
        writer = self.rasterFromValue((1, 1, 1), 10, 'inraster.tif')
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_DATA_MIN: 20,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertArrayEqual(20, array)

    def test_max(self):
        writer = self.rasterFromValue((1, 1, 1), 10, 'inraster.tif')
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_DATA_MAX: 5,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertArrayEqual(5, array)

    def test_noDataValue(self):
        writer = self.rasterFromArray([[[0, 10]]], 'inraster.tif')
        writer.setNoDataValue(0)
        writer.close()
        alg = PrepareRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_NO_DATA_VALUE: -123,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertArrayEqual(np.array([[[-123, 10]]]), array)
