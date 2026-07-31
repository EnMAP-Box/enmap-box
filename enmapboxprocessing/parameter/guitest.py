from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm

qgsApp = start_app()

initAll()
enmapBox = EnMAPBox()
enmapBox.openExampleData(mapWindows=1)

enmapBox.showProcessingAlgorithmDialog(
    PrepareUnsupervisedDatasetFromCodeAlgorithm(), parameters=None
)

qgsApp.exec()
