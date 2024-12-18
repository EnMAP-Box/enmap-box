import numpy as np
from qgis.core import QgsCoordinateReferenceSystem

from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.libraryfromclassificationdatasetalgorithm import \
    LibraryFromClassificationDatasetAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import Category, ClassifierDump

start_app()
initAll()


class TestLibraryFromClassificationDatasetAlgorithm(TestCase):

    def test_withGeometry(self):
        categories = [Category(1, 'class A', '#f00'), Category(2, 'class B', '#0f0')]
        dump = ClassifierDump(
            categories=categories,
            features=['feature 1', 'feature 2', 'feature 3'],
            X=np.array([(1, 2, 3), (10, 11, 12), (20, 21, 22)]),
            y=np.array([[1], [2], [1]]),
            classifier=None,
            locations=np.array([(1, 1), (2, 2), (3, 3)]),
            crs=QgsCoordinateReferenceSystem.fromEpsgId(4326).toWkt()
        )
        dump.write(self.filename('dataset.pkl'))

        alg = LibraryFromClassificationDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('dataset.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.geojson')
        }
        self.runalg(alg, parameters)

    def test_withOutGeometry(self):
        categories = [Category(1, 'class A', '#f00'), Category(2, 'class B', '#0f0')]
        dump = ClassifierDump(
            categories=categories,
            features=['feature 1', 'feature 2', 'feature 3'],
            X=np.array([(1, 2, 3), (10, 11, 12), (20, 21, 22)]),
            y=np.array([[1], [2], [1]]),
        )
        dump.write(self.filename('dataset.pkl'))

        alg = LibraryFromClassificationDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('dataset.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.geojson')
        }
        self.runalg(alg, parameters)
