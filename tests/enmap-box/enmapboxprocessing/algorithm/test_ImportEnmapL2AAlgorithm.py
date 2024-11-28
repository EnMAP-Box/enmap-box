import numpy as np

from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportEnmapL2AAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A.vrt'),
        }
        result = self.runalg(alg, parameters)
        self.assertAlmostEqual(
            -11535788939.969,
            np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float), 3
        )

    def test_OrderByDetectorOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.OrderByDetectorOverlapOption,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_OrderByWavelength.vrt'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(224, RasterReader(result[alg.P_OUTPUT_RASTER]).bandCount())

    def test_OrderByWavelengthOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.OrderByWavelengthOverlapOption,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_OrderByWavelength.vrt'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(224, RasterReader(result[alg.P_OUTPUT_RASTER]).bandCount())

    def test_VnirOnlyOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.VnirOnlyOverlapOption,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_VnirOnly.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(214, reader.bandCount())

    def test_SwirOnlyOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.SwirOnlyOverlapOption,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_SwirOnly.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(212, reader.bandCount())

    def test_MovingAverageFilterOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.MovingAverageFilterOverlapOption,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_MovingAverageFilter.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(224, reader.bandCount())

    def test_setBadBandList(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_SET_BAD_BANDS: True,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_BBL.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        bbl = [reader.badBandMultiplier(bandNo) for bandNo in reader.bandNumbers()]
        gold = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1]
        self.assertListEqual(gold, bbl)

    def test_excludeBadBandList(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_SET_BAD_BANDS: True,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_BadBandsExcluded.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(190, reader.bandCount())

    def test_ardProduct(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_ARD_MetadataXml,
            alg.P_SET_BAD_BANDS: True,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A.tif'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A.tif'),
        }
        result = self.runalg(alg, parameters)
