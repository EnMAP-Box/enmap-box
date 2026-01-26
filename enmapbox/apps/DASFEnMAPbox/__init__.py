from enmapbox.gui.applications import EnMAPBoxApplication
from DASFEnMAPbox.processingalgorithm import DASFretrievalAlgorithm

def enmapboxApplicationFactory(enmapBox):
    return [DASFretrievalApp(enmapBox)]

class DASFretrievalApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'DASF retrieval'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def processingAlgorithms(self):
        return [DASFretrievalAlgorithm()]
