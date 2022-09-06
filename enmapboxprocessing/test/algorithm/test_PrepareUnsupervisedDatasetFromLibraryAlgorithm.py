from enmapbox.exampledata import library_gpkg
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromlibraryalgorithm import \
    PrepareUnsupervisedDatasetFromLibraryAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingException


class TestPrepareUnsupervisedDatasetFromLibraryAlgorithm(TestCase):

    def test_default(self):
        alg = PrepareUnsupervisedDatasetFromLibraryAlgorithm()
        parameters = {
            alg.P_LIBRARY: library_gpkg,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))

    def test_selectBinaryField(self):
        alg = PrepareUnsupervisedDatasetFromLibraryAlgorithm()
        parameters = {
            alg.P_LIBRARY: library_gpkg,
            alg.P_FIELD: 'profiles',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((75, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))

    def test_wrongProfileField(self):
        alg = PrepareUnsupervisedDatasetFromLibraryAlgorithm()
        parameters = {
            alg.P_LIBRARY: library_gpkg,
            alg.P_FIELD: 'level_1',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Profiles field must be Binary: level_1', str(error))
