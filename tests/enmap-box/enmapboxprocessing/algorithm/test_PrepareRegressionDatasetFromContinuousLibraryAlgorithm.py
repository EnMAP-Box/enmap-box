from qgis.core import QgsGeometry, QgsPointXY, QgsVectorLayer, QgsCoordinateReferenceSystem

from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuouslibraryalgorithm import \
    PrepareRegressionDatasetFromContinuousLibraryAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import library_gpkg


class TestPrepareRegressionDatasetFromContinuousLibraryAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromContinuousLibraryAlgorithm()
        parameters = {
            alg.P_CONTINUOUS_LIBRARY: library_gpkg,  # todo use better dataset (wait for #1036)
            alg.P_TARGET_FIELDS: ['fid'],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual((75, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))

        # todo implement more tests, wait for issue #1036

    def test_locations(self):
        # create data
        values = {'profiles': {'y': [1, 2, 3]}, 'target': 1}
        geometry = QgsGeometry.fromPointXY(QgsPointXY(1, 2))
        writer = LibraryDriver().createFromData([values], [geometry])
        filename = self.filename('library2.geojson')
        writer.writeToSource(filename)
        layer = QgsVectorLayer(filename)

        alg = PrepareRegressionDatasetFromContinuousLibraryAlgorithm()
        parameters = {
            alg.P_CONTINUOUS_LIBRARY: layer,
            alg.P_TARGET_FIELDS: ['target'],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(
            QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsCoordinateReferenceSystem.fromWkt(dump.crs)
        )
        self.assertEqual((1, 2), tuple(dump.locations[0]))


"""    def test_selectBinaryField(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            alg.P_FIELD: 'profiles',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual((75, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))

    def test_wrongCategoryField(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            # alg.P_FIELD: 'profiles',
            alg.P_CATEGORY_FIELD: 'profiles',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Unable to derive categories from field: profiles', str(error))

    def test_wrongProfileField(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            alg.P_FIELD: 'level_1',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Profiles field must be Binary: level_1', str(error))
"""
