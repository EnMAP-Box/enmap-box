import unittest
from os.path import normpath

import numpy as np
from osgeo import gdal

from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap, landcover_polygon, hires
from qgis.core import Qgis

start_app()


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestRasterMathAlgorithm(TestCase):

    def test_writeToDefaultOutput1(self):
        alg = RasterMathAlgorithm()

        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: alg.P_OUTPUT_RASTER + ' = R1',  # Option 1: use the default output raster name
            alg.P_OUTPUT_RASTER: self.filename('enmap.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908457369, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
        self.assertEqual(self.filename('enmap.tif'), RasterReader(result[alg.P_OUTPUT_RASTER]).source())

    def test_writeToDefaultOutput2(self):
        alg = RasterMathAlgorithm()

        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'enmap = R1',  # Option 2: use the selected output raster name, e.g. 'enmap'
            alg.P_OUTPUT_RASTER: self.filename('enmap.tif')  # basename matches identifier
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908457369, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
        self.assertEqual(
            normpath(self.filename('enmap.tif')), normpath(RasterReader(result[alg.P_OUTPUT_RASTER]).source()))
        self.assertIsNone(result.get('enmap'))

    def test_writeToAdditionalOutputs(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'test = R1\n'  # define new outputs by using an identifier, e.g. test -> test.tif
                        'test2 = R1',
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')  # only used to define the folder!
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908457369, np.sum(RasterReader(result['test']).array(), dtype=float))
        self.assertEqual(14908457369, np.sum(RasterReader(result['test2']).array(), dtype=float))

    def test_expression(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'R1',
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908457369, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
        self.assertTrue(len(result) == 1)

    def test_expression_withAt(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'R1@1',
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29424494, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
        self.assertTrue(len(result) == 1)

    def test_inputs_lists(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_RS: [enmap, enmap],
            alg.P_CODE: 'data = np.average(RS, axis=0)\n'
                        'mask = np.all(RSMask, axis=0)',
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908457369, np.sum(RasterReader(result['data']).array(), dtype=float))
        self.assertEqual(12594966, np.sum(RasterReader(result['mask']).array(), dtype=float))

    def test_input_list_metadata(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_RS: [enmap, enmap],
            alg.P_CODE: 'for reader in RS_:\n'  # we have to use the explicite RS_ handle
                        '    feedback.pushInfo(reader.noDataValue())',
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)

    def test_vector(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_V1: landcover_polygon,
            alg.P_CODE: 'V1',  # use as a 0/1 mask
            alg.P_OUTPUT_RASTER: self.filename('landcover_mask.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2028, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()))
        self.assertTrue(len(result) == 1)

    def test_vector_withAt(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_V1: landcover_polygon,
            alg.P_CODE: 'vector1 = V1@"None"\n'  # use as a 0/1 mask
                        'vector2 = V1\n'  # The same mask!
                        'vector3 = V1@"level_3_id"',

            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2028, np.sum(RasterReader(result['vector1']).array()))
        self.assertEqual(2028, np.sum(RasterReader(result['vector2']).array()))

    def test_with_overlap(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: hires,
            alg.P_CODE: 'from scipy.ndimage import gaussian_filter\n'
                        'outputRaster = gaussian_filter(R1, sigma=3)\n',
            alg.P_OUTPUT_RASTER: self.filename('raster.tif'),
            alg.P_OVERLAP: 15
        }
        result = self.runalg(alg, parameters)
        # self.assertEqual(631209052, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))

    def test_stats(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'hist, bin_edges = np.histogram(R1, bins=10, range=(0, 10000))\n'
                        'for a, b, n in zip(bin_edges[:-1], bin_edges[1:], hist):\n'
                        "   feedback.pushInfo(f'[{a}, {b}]: {n}')\n",
            alg.P_MONOLITHIC: True,
            alg.P_OUTPUT_RASTER: self.filename('info.tif')
        }
        self.runalg(alg, parameters)

    def test_getAndSetMetadata(self):
        alg = RasterMathAlgorithm()
        orig = RasterReader(enmap)
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'raster = R1\n'
                        'raster.setNoDataValue(R1.noDataValue())\n'
                        'raster.setMetadata(R1.metadata())\n'
                        'for bandNo in range(1, R1.bandCount() + 1):\n'
                        '    raster.setBandName(R1.bandName(bandNo), bandNo)\n',
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(14908457369, np.sum(reader.array(), dtype=float))
        self.assertEqual(orig.noDataValue(), reader.noDataValue())
        self.assertEqual(orig.bandName(1), reader.bandName(1))

    def test_externalRasterLayer(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_CODE: f"# enmap := QgsRasterLayer(r'{enmap}')\n"
                        'enmap',
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(14908457369, np.sum(reader.array(), dtype=float))

    def test_externalRasterLayer_withAt(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_CODE: f"# enmap := QgsRasterLayer(r'{enmap}')\n"
                        'raster1 = enmap@42\n'  # band 42 by index
                        'raster2 = enmapMask@42\n'
                        'raster3 = enmap@685nm\n'  # band 42 by wavelength
                        'raster4 = enmapMask@685nm\n'
                        'raster5 = enmap@"band 49 (0.685000 Micrometers)"\n'  # band 42 by name
                        'raster6 = enmapMask@"band 49 (0.685000 Micrometers)"\n'
                        'raster7 = enmap@111|10:20|^15:100|^12\n'  # band list [10, 11, 13, 14, 111] by number ranges
                        'raster8 = enmapMask@111|10:20|^15:100|^12\n'
                        'raster9 = enmap@^10:100\n'  # band list [1,...,9, 100,...] by number ranges
                        'raster10 = enmapMask@^10:100\n'
                        'dummy = enmap.noDataValue()',  # using the reader shall not trigger reading all data!

            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        # self.assertEqual(47481925, np.sum(RasterReader(result['raster1']).array()))
        # self.assertEqual(71158, np.sum(RasterReader(result['raster2']).array()))
        # self.assertEqual(47481925, np.sum(RasterReader(result['raster3']).array()))
        # self.assertEqual(71158, np.sum(RasterReader(result['raster4']).array()))
        # self.assertEqual(47481925, np.sum(RasterReader(result['raster5']).array()))
        # self.assertEqual(71158, np.sum(RasterReader(result['raster6']).array()))
        # self.assertEqual(np.sum(RasterReader(enmap).array(bandList=[10, 11, 13, 14, 111]), dtype=float),
        #                 np.sum(RasterReader(result['raster7']).array(), dtype=float))
        # self.assertEqual(71158. * 5, np.sum(RasterReader(result['raster8']).array(), dtype=float))
        # bandList = list(range(1, 10)) + list(range(100, 178))
        # self.assertEqual(np.sum(RasterReader(enmap).array(bandList=bandList), dtype=float),
        #                 np.sum(RasterReader(result['raster9']).array(), dtype=float))
        # self.assertEqual(71158. * len(bandList), np.sum(RasterReader(result['raster10']).array(), dtype=float))

    def test_externalVectorLayer_field(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_CODE: f"# landcover := QgsVectorLayer(r'{landcover_polygon}')\n"
                        'landcover@"level_3_id"',
            alg.P_GRID: enmap,
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(5260, np.sum(reader.array(), dtype=float))

    def test_externalVectorLayer_mask(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_CODE: f"# landcover := QgsVectorLayer(r'{landcover_polygon}')\n"
                        'landcover',
            alg.P_GRID: enmap,
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(2028, np.sum(reader.array(), dtype=float))

    def test_floatInput(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'raster=R1',
            alg.P_FLOAT_INPUT: True,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(Qgis.DataType.Float32, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType(1))

    def test_not_floatInput(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'raster=R1',
            alg.P_FLOAT_INPUT: False,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(Qgis.DataType.Int16, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType(1))

    def _test_debug_issue1245(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'raster=R1.astype(np.int64)',
            alg.P_FLOAT_INPUT: False,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(Qgis.DataType.Float64, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType(1))

    def test_replaceNoDataValue(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'raster=R1',
            alg.P_NO_DATA_VALUE: -42,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertArrayEqual(-42, RasterReader(result[alg.P_OUTPUT_RASTER]).array(0, 0, 1, 1))

    def test_notReplaceNoDataValue(self):
        alg = RasterMathAlgorithm()
        parameters = {
            alg.P_R1: enmap,
            alg.P_CODE: 'raster=R1',
            alg.P_NO_DATA_VALUE: None,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertArrayEqual(-99, RasterReader(result[alg.P_OUTPUT_RASTER]).array(0, 0, 1, 1))
