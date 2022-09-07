import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.convexhullalgorithm import ConvexHullAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import QgsRectangle


class TestTranslateAlgorithm(TestCase):

    def test_prisma(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_EXTENT: QgsRectangle(384340.7, 5809773.2, 384771.5, 5810088.0),
            alg.P_CREATION_PROFILE: alg.DefaultVrtCreationProfile,
            alg.P_OUTPUT_RASTER: self.filename('subset.vrt'),
        }
        result = self.runalg(alg, parameters)

        alg = ConvexHullAlgorithm()
        parameters = {
            alg.P_RASTER: self.filename('subset.vrt'),
            alg.P_X_UNITS: alg.BandNumberUnits,
            alg.P_OUTPUT_CONVEX_HULL: self.filename('convexHull.tif'),
            alg.P_OUTPUT_CONTINUUM_REMOVED: self.filename('continuumRemoved.tif')
        }
        result = self.runalg(alg, parameters)

        self.assertEqual(48631695, np.sum(RasterReader(result[alg.P_OUTPUT_CONVEX_HULL]).array()))
        self.assertEqual(22883, round(np.sum(RasterReader(result[alg.P_OUTPUT_CONTINUUM_REMOVED]).array())))
