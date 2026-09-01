import sys
from os.path import basename, join, dirname

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.processing.algorithmdialog import AlgorithmDialog
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromfilealgorithm import \
    PrepareUnsupervisedDatasetFromFileAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromjsonalgorithm import \
    PrepareUnsupervisedDatasetFromJsonAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromlibraryalgorithm import \
    PrepareUnsupervisedDatasetFromLibraryAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromrasteralgorithm import \
    PrepareUnsupervisedDatasetFromRasterAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromvectorandfieldsalgorithm import \
    PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QMenu, QMessageBox
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMessageLog, Qgis
from qgis.gui import (
    QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui, QgsFileWidget
)


class ProcessingParameterSkopsFileUnsupervisedDatasetWidget(QWidget):
    mFile: QgsFileWidget
    mCreate: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(join(dirname(__file__), 'processingparameterskopsfilewidget.ui'), self)

        self.menu = QMenu()
        self.menu.setToolTipsVisible(True)

        for alg, icon in [
            (PrepareUnsupervisedDatasetFromRasterAlgorithm(),
             QIcon(':/images/themes/default/mIconRaster.svg')),

            (PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm(),
             QIcon(':/images/themes/default/mActionOpenTable.svg')),

            (PrepareUnsupervisedDatasetFromLibraryAlgorithm(),
             QIcon(':/qps/ui/icons/speclib.svg')),

            (PrepareUnsupervisedDatasetFromCodeAlgorithm(),
             QIcon(':/images/themes/default/mIconPythonFile.svg')),

            (PrepareUnsupervisedDatasetFromFileAlgorithm(),
             QIcon(':/images/themes/default/mIconFile.svg')),

            (PrepareUnsupervisedDatasetFromJsonAlgorithm(),
             QIcon(':/images/themes/default/mIconFieldJson.svg'))
        ]:
            action = self.menu.addAction(alg.displayName())
            action.setIcon(icon)
            action.setText(alg.displayName())
            action.triggered.connect(self.onCreateClicked)
            action.alg = alg

        if EnMAPBox.instance() is not None:
            self.menu.addSeparator()
            for filename in EnMAPBox.instance().dataSources('MODEL', True):
                if not filename.endswith('.skops'):
                    continue
                try:
                    dump = TransformerDump(**Utils.modelLoad(filename))
                    samples, features = dump.X.shape
                except Exception as ex:
                    print(f'Unable to open .skop file: {ex}', file=sys.stderr)
                    continue

                action = self.menu.addAction('')
                action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                action.setText(basename(filename) + f' ({samples} samples, {features} features)')
                action.setToolTip(rf'<html><head/><body><p>{filename}</p></body></html>')
                action.triggered.connect(self.onFilenameClicked)
                action.filename = filename

        self.mCreate.setMenu(self.menu)

    def value(self) -> str:
        return self.mFile.filePath()

    def setValue(self, value):
        self.mFile.setFilePath(value)

    filePath = value
    setFilePath = setValue

    def onCreateClicked(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()

        class AlgorithmDialogWrapper(AlgorithmDialog):
            def finish(self_, successful, result, context, feedback, in_place=False):
                super().finish(successful, result, context, feedback, in_place)
                if successful:
                    filename = result['outputUnsupervisedDataset']
                    self.mFile.setFilePath(filename)

                    dump = TransformerDump(**Utils.modelLoad(filename))
                    samples, features = dump.X.shape

                    # add to the list!
                    action = self.menu.addAction(alg.displayName())
                    action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                    action.setText(basename(filename) + f' ({samples} samples, {features} features)')
                    action.setToolTip(rf'<html><head/><body><p>{filename}</p></body></html>')
                    action.triggered.connect(self.onFilenameClicked)
                    action.filename = filename

                    self_.close()

        alg = self.sender().alg
        if enmapBox is None:
            QMessageBox.information(self, 'Information', 'EnMAP-Box not running.')
            return

        enmapBox.showProcessingAlgorithmDialog(alg, modal=True, wrapper=AlgorithmDialogWrapper)

    def onFilenameClicked(self):
        filename = self.sender().filename
        self.mFile.setFilePath(filename)


class ProcessingParameterSkopsFileUnsupervisedDatasetWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):

    def createWidget(self):
        return ProcessingParameterSkopsFileUnsupervisedDatasetWidget()

    def setWidgetValue(self, value, context):
        widget = self.wrappedWidget()
        widget.setValue(value)

    def widgetValue(self):
        widget = self.wrappedWidget()
        return widget.value()


class ProcessingParameterSkopsFileUnsupervisedDatasetWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterSkopsFileUnsupervisedDatasetWidget'

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        return ProcessingParameterSkopsFileUnsupervisedDatasetWidgetWrapper(parameter, widget_type)

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)
