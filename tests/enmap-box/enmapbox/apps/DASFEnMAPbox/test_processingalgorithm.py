from DASFEnMAPbox import DASFretrievalAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap_potsdam


class TestDASFretrievalAlgorithm(TestCase):

    def test(self):
        alg = DASFretrievalAlgorithm()
        parameters = {
            alg.P_INPUT: enmap_potsdam,
            alg.P_OUTPUT: self.filename('DASF.bsq'),
            alg.P_Retrieval_Quality: self.filename('DASF_retrievalQuality.bsq'),
            alg.P_CSC: self.filename('CSC.bsq')
        }
        self.runalg(alg, parameters)
