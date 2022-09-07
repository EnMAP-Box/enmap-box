from enmapbox.exampledata import library_gpkg
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedlibraryalgorithm import \
    PrepareClassificationDatasetFromCategorizedLibraryAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingException


class TestPrepareClassificationDatasetFromCategorizedLibrary(TestCase):

    def test_default(self):
        alg = PrepareClassificationDatasetFromCategorizedLibraryAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_LIBRARY: library_gpkg,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual((75, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))

    def test_selectBinaryField(self):
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
