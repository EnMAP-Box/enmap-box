from os import listdir
from os.path import join, dirname, exists, basename, isdir, isfile

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mimedata import MDF_URILIST
from enmapboxprocessing.algorithm.importdesisl1balgorithm import ImportDesisL1BAlgorithm
from enmapboxprocessing.algorithm.importdesisl1calgorithm import ImportDesisL1CAlgorithm
from enmapboxprocessing.algorithm.importdesisl2aalgorithm import ImportDesisL2AAlgorithm
from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.algorithm.importlandsatl2algorithm import ImportLandsatL2Algorithm
from enmapboxprocessing.algorithm.importprismal1algorithm import ImportPrismaL1Algorithm
from enmapboxprocessing.algorithm.importprismal2balgorithm import ImportPrismaL2BAlgorithm
from enmapboxprocessing.algorithm.importprismal2calgorithm import ImportPrismaL2CAlgorithm
from enmapboxprocessing.algorithm.importprismal2dalgorithm import ImportPrismaL2DAlgorithm
from enmapboxprocessing.algorithm.importproductsdraganddropsupport import AlgorithmDialogWrapper
from enmapboxprocessing.algorithm.importsentinel2l2aalgorithm import ImportSentinel2L2AAlgorithm
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QEvent
from qgis.PyQt.QtWidgets import QLabel
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer
from qgis.gui import QgsDockWidget, QgisInterface
from typeguard import typechecked


@typechecked
class SensorProductImportDockWidget(QgsDockWidget):
    mDropArea: QLabel

    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        # set from outside
        self.interface = None
        self.interfaceType = None

        self.mDropArea.installEventFilter(self)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.DragEnter):
            event.accept()
            return True

        if (event.type() == QEvent.Drop):
            mimeData = event.mimeData()

            if MDF_URILIST in mimeData.formats():
                for url in mimeData.urls():
                    url = url.url().replace('file:///', '')
                    self.openProduct(url)
                    break  # diguest only one file
            return True
        return False

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self):
        return self.interface

    def setInterface(self, interface):
        self.interface = interface
        if isinstance(interface, EnMAPBox):
            self.interfaceType = 0
        elif isinstance(interface, QgisInterface):
            self.interfaceType = 1
        else:
            raise ValueError()

    def openProduct(self, url: str):

        algs = [
            ImportDesisL1BAlgorithm(),
            ImportDesisL1CAlgorithm(),
            ImportDesisL2AAlgorithm(),
            ImportEnmapL1BAlgorithm(),
            ImportEnmapL1CAlgorithm(),
            ImportEnmapL2AAlgorithm(),
            ImportLandsatL2Algorithm(),
            ImportPrismaL1Algorithm(),
            ImportPrismaL2BAlgorithm(),
            ImportPrismaL2CAlgorithm(),
            ImportPrismaL2DAlgorithm(),
            ImportSentinel2L2AAlgorithm()
        ]
        layers = list()
        filename = None
        # check URL
        for alg in algs:
            if isfile(url):
                if alg.isValidFile(url):
                    filename = url
                    break
            elif isdir(url):
                for name in listdir(url):
                    url2 = join(url, name)
                    if alg.isValidFile(url2):
                        filename = url2
                        break
                if filename is not None:
                    break

        # check URL directory
        if filename is None:
            for alg in algs:
                for name in listdir(dirname(url)):
                    url2 = join(dirname(url), name)
                    if alg.isValidFile(url2):
                        filename = url2
                        break
                if filename is not None:
                    break

        if filename is None:
            return

        parameters = alg.defaultParameters(filename)
        alreadyExists = True
        for key, value in parameters.items():
            if key.startswith('output'):
                alreadyExists &= exists(value)
        if not alreadyExists:
            dialog: AlgorithmDialogWrapper = EnMAPBox.showProcessingAlgorithmDialog(
                alg, parameters, True, True, AlgorithmDialogWrapper, False
            )
            if not dialog.finishedSuccessful:
                return
            result = dialog.finishResult
            result = {}  # results will be opened by the processing framework

        else:
            result = {key: value for key, value in parameters.items()
                      if key.startswith('output')}

        for key, value in result.items():
            if parameters[key] is None or value is None:
                continue
            layer = QgsRasterLayer(parameters[key], basename(value))
            layers.append(layer)

        if self.interfaceType == self.EnmapBoxInterface:
            self.enmapBoxInterface().addMapLayers(layers)
        elif self.interfaceType == self.QgisInterface:
            QgsProject.instance().addMapLayers(layers)
