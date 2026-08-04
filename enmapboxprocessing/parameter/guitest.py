from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.classificationworkflowalgorithm import ClassificationWorkflowAlgorithm
from enmapboxprocessing.algorithm.exportdatasettofilesalgorithm import ExportDatasetToFilesAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
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
if 0:
    # Classifier
    enmapBox.showProcessingAlgorithmDialog(
        ClassificationWorkflowAlgorithm(), parameters=None
    )

    # ProcessingParameterRasterMathCodeEditWidgetWrapper
if 0:
    enmapBox.showProcessingAlgorithmDialog(
        RasterMathAlgorithm(), parameters=None
    )

# ProcessingParameterSkopsFileWidgetWrapper
if 0:
    enmapBox.showProcessingAlgorithmDialog(
        ExportDatasetToFilesAlgorithm(), parameters=None
    )

# ProcessingParameterSkopsFileClassificationDatasetWidgetWrapper
if 0:
    enmapBox.showProcessingAlgorithmDialog(
        ClassificationWorkflowAlgorithm(), parameters=None
    )

# ProcessingParameterSkopsFileRegressionDatasetWidgetWrapper
if 1:
    enmapBox.showProcessingAlgorithmDialog(
        RegressionWorkflowAlgorithm(), parameters=None
    )
# ProcessingParameterSkopsFileUnsupervisedDatasetWidgetWrapper


qgsApp.exec()
