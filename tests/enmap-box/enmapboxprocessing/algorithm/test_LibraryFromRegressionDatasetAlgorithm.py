import numpy as np
from qgis.core import QgsCoordinateReferenceSystem

from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.libraryfromregressiondatasetalgorithm import LibraryFromRegressionDatasetAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump, Target

start_app()
initAll()


class TestLibraryFromRegressionDatasetAlgorithm(TestCase):

    def test_withGeometry(self):
        targets = [Target('target A', '#f00'), Target('target B', '#0f0')]
        dump = RegressorDump(
            targets=targets,
            features=['feature 1', 'feature 2', 'feature 3'],
            X=np.array([(1, 2, 3), (10, 11, 12), (20, 21, 22)]),
            y=np.array([[1, 10], [2, 20], [3, 30]]),
            locations=np.array([(1, 1), (2, 2), (3, 3)]),
            crs=QgsCoordinateReferenceSystem.fromEpsgId(4326).toWkt()
        )
        dump.write(self.filename('dataset.pkl'))

        alg = LibraryFromRegressionDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('dataset.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.geojson')
        }
        self.runalg(alg, parameters)

    def test_withOutGeometry(self):
        targets = [Target('target A', '#f00'), Target('target B', '#0f0')]
        dump = RegressorDump(
            targets=targets,
            features=['feature 1', 'feature 2', 'feature 3'],
            X=np.array([(1, 2, 3), (10, 11, 12), (20, 21, 22)]),
            y=np.array([[1, 10], [2, 20], [3, 30]])
        )
        dump.write(self.filename('dataset.pkl'))

        alg = LibraryFromRegressionDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('dataset.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.geojson')
        }
        self.runalg(alg, parameters)
