from enmapbox.gui.applications import EnMAPBoxApplication
from hzg_onns.processingalgorithm import OnnsProcessingAlgorithm

def enmapboxApplicationFactory(enmapBox):
    return [OnnsApp(enmapBox)]

class OnnsApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'ONNS'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def processingAlgorithms(self):
        return [OnnsProcessingAlgorithm()]
