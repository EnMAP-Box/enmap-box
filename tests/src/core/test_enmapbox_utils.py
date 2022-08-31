from qgis.core import QgsRasterLayer

from enmapbox.exampledata import enmap
from enmapbox.testing import EnMAPBoxTestCase
from enmapbox.utils import findBroadBand
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm


class TestEnmapboxUtils(EnMAPBoxTestCase):

    def test_findBroadBand(self):
        gold = [None, 8, 21, 39, 45, 50, 56, 66, 62, 116, 151, None, None]
        lead = [findBroadBand(QgsRasterLayer(enmap), name, True)
                for name in CreateSpectralIndicesAlgorithm.WavebandMapping]
        self.assertListEqual(gold, lead)

        gold = [1, 8, 21, 39, 45, 50, 56, 66, 62, 116, 151, 177, 177]
        lead = [findBroadBand(QgsRasterLayer(enmap), name, False)
                for name in CreateSpectralIndicesAlgorithm.WavebandMapping]
        self.assertListEqual(gold, lead)
