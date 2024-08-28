from enmapboxprocessing.algorithm.landcoverchangestatisticsalgorithm import LandCoverChangeStatisticsAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import landcover_map_l3, landcover_map_l2
from qgis.core import QgsRasterLayer


class TestLandCoverChangeStatisticsAlgorithm(TestCase):

    def test(self):
        alg = LandCoverChangeStatisticsAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATIONS: [
                QgsRasterLayer(landcover_map_l2, 'Level 2'), QgsRasterLayer(landcover_map_l3, 'Level 3')
            ],
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)
