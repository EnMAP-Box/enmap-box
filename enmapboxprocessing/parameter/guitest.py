from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.classificationworkflowalgorithm import ClassificationWorkflowAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.regressionworkflowalgorithm import RegressionWorkflowAlgorithm
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

if 0:
    # ProcessingParameterCreationProfileWidgetWrapper
    enmapBox.showProcessingAlgorithmDialog(
        SaveRasterAsAlgorithm(), parameters=None
    )

# ProcessingParameterEstimatorCodeEditWrapper
if 0:
    # Regressor
    enmapBox.showProcessingAlgorithmDialog(
        RegressionWorkflowAlgorithm(), parameters=None
    )
if 1:
    # Classifier
    enmapBox.showProcessingAlgorithmDialog(
        ClassificationWorkflowAlgorithm(), parameters=None
    )

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
