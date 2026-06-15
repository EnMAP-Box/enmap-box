from awi_ocpft.processingalgorithm import OCPFTProcessingAlgorithm
from enmapbox.gui.applications import EnMAPBoxApplication


def enmapboxApplicationFactory(enmapBox):
    return [OcpftApp(enmapBox)]


class OcpftApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'OC-PFT'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def processingAlgorithms(self):
        return [OCPFTProcessingAlgorithm()]
