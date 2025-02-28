import unittest

from osgeo import gdal

from enmapboxprocessing.algorithm.regressorperformancealgorithm import RegressorPerformanceAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import regressorDumpPkl, regressorDumpSingleTargetPkl


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestRegressorPerformanceAlgorithm(TestCase):

    def test_trainPerformance_multiTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpPkl,
            alg.P_DATASET: regressorDumpPkl,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train_multitarget.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance_multiTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpPkl,
            alg.P_DATASET: regressorDumpPkl,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval_multitarget.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_trainPerformance_singleTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpSingleTargetPkl,
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train_singletarget.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance_singleTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpSingleTargetPkl,
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_NFOLD: 10,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval_singletarget.html')
        }
        self.runalg(alg, parameters)
        # check the result manually
