from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.classificationworkflowalgorithm import ClassificationWorkflowAlgorithm
from enmapboxprocessing.algorithm.exportdatasettofilesalgorithm import ExportDatasetToFilesAlgorithm
from enmapboxprocessing.algorithm.fitpcaalgorithm import FitPcaAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
from enmapboxprocessing.algorithm.regressionworkflowalgorithm import RegressionWorkflowAlgorithm
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.testcase import TestCase
from enmapbox import initAll

qgsApp = start_app()
initAll()


class TestCustomProcessingParameterWidgets(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)

        # we create several algos, which are using those widgets

        if 1:
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
        if 1:
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
        if 1:
            enmapBox.showProcessingAlgorithmDialog(
                RasterMathAlgorithm(), parameters=None
            )

        # ProcessingParameterSkopsFileWidgetWrapper
        if 1:
            enmapBox.showProcessingAlgorithmDialog(
                ExportDatasetToFilesAlgorithm(), parameters=None
            )

        # ProcessingParameterSkopsFileClassificationDatasetWidgetWrapper
        if 1:
            enmapBox.showProcessingAlgorithmDialog(
                ClassificationWorkflowAlgorithm(), parameters=None
            )

        # ProcessingParameterSkopsFileRegressionDatasetWidgetWrapper
        if 1:
            enmapBox.showProcessingAlgorithmDialog(
                RegressionWorkflowAlgorithm(), parameters=None
            )

        # ProcessingParameterSkopsFileUnsupervisedDatasetWidgetWrapper
        if 1:
            enmapBox.showProcessingAlgorithmDialog(
                FitPcaAlgorithm(), parameters=None
            )

        if not False:
            qgsApp.exec()

        self.dispose_widget(enmapBox.ui)
