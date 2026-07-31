from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm

qgsApp = start_app()

initAll()
enmapBox = EnMAPBox()
enmapBox.openExampleData(mapWindows=1)

if 0:
    # ProcessingParameterCodeEditWidgetWrapper
    enmapBox.showProcessingAlgorithmDialog(
        PrepareUnsupervisedDatasetFromCodeAlgorithm(), parameters=None
    )

if 1:
    # ProcessingParameterCreationProfileWidgetWrapper
    enmapBox.showProcessingAlgorithmDialog(
        SaveRasterAsAlgorithm(), parameters=None
    )

# ProcessingParameterEstimatorCodeEditWrapper
#
# ProcessingParameterRasterMathCodeEditWidgetWrapper
#
# ProcessingParameterSkopsFileClassificationDatasetWidgetWrapper
#
# ProcessingParameterSkopsFileRegressionDatasetWidgetWrapper
#
# ProcessingParameterSkopsFileUnsupervisedDatasetWidgetWrapper
#
# ProcessingParameterSkopsFileWidgetWrapper
qgsApp.exec()
