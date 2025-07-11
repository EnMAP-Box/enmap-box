from os import makedirs
from os.path import dirname, exists

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.cleanupvrtalgorithm import CleanupVrtAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestCleanupVrtAlgorithm(TestCase):

    def test(self):
        writer = self.rasterFromRange((1, 2, 2), 'source.tif')
        writer.close()

        filename = self.filename('VRT/target.vrt')
        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        gdal.Translate(filename, writer.source(), format='VRT')

        alg = CleanupVrtAlgorithm()
        parameters = {
            alg.P_VRT: filename,
        }
        self.runalg(alg, parameters)

        array = RasterReader(filename).array()[0]
        self.assertArrayEqual(np.array([[0, 1], [2, 3]]), array)
