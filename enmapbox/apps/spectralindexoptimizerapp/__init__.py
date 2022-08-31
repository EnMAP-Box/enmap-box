from enmapbox.gui.applications import EnMAPBoxApplication
from spectralindexoptimizerapp.processingalgorithm import SpectralIndexOptimizerProcessingAlgorithm

def enmapboxApplicationFactory(enmapBox):
    return [SpectralIndexOptimizerApp(enmapBox)]

class SpectralIndexOptimizerApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'Spectral Index Optimizer'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def processingAlgorithms(self):
        return [SpectralIndexOptimizerProcessingAlgorithm()]

# C:\Users\buddenba\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\enmapboxplugin\enmapbox\apps