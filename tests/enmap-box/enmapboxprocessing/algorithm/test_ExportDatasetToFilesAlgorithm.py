from enmapboxprocessing.algorithm.exportdatasettofilesalgorithm import ExportDatasetToFilesAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpSkops, regressorDumpSkops


class TestExportDatasetToFilesAlgorithm(TestCase):

    def test_classificationDataset(self):
        alg = ExportDatasetToFilesAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpSkops,
            alg.P_OUTPUT_FEATURE_FILE: self.filename('features.csv'),
            alg.P_OUTPUT_VALUE_FILE: self.filename('labels.csv')
        }
        self.runalg(alg, parameters)

    def test_regressionDataset(self):
        alg = ExportDatasetToFilesAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpSkops,
            alg.P_OUTPUT_FEATURE_FILE: self.filename('features.csv'),
            alg.P_OUTPUT_VALUE_FILE: self.filename('labels.csv')
        }

        self.runalg(alg, parameters)
