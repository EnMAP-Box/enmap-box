import traceback
from os.path import exists, basename
from typing import List

from enmapboxprocessing.algorithm.importdesisl1balgorithm import ImportDesisL1BAlgorithm
from enmapboxprocessing.algorithm.importdesisl1calgorithm import ImportDesisL1CAlgorithm
from enmapboxprocessing.algorithm.importdesisl2aalgorithm import ImportDesisL2AAlgorithm
from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.algorithm.importlandsatl2algorithm import ImportLandsatL2Algorithm
from enmapboxprocessing.algorithm.importprismal1algorithm import ImportPrismaL1Algorithm
from enmapboxprocessing.algorithm.importprismal2dalgorithm import ImportPrismaL2DAlgorithm
from enmapboxprocessing.algorithm.importsentinel2l2aalgorithm import ImportSentinel2L2AAlgorithm
from processing import AlgorithmDialog
from qgis.core import QgsRasterLayer, QgsMapLayer


class AlgorithmDialogWrapper(AlgorithmDialog):
    def __init__(self, *args, **kwargs):
        AlgorithmDialog.__init__(self, *args, **kwargs)
        self.finishedSuccessful = False
        self.finishResult = None

    def finish(self, successful, result, context, feedback, in_place=False):
        super().finish(successful, result, context, feedback, in_place)
        self.finishedSuccessful = successful
        self.finishResult = result
        if successful:
            self.close()


def tryToImportSensorProducts(filename: str) -> List[QgsMapLayer]:
    try:
        algs = [
            ImportDesisL1BAlgorithm(),
            ImportDesisL1CAlgorithm(),
            ImportDesisL2AAlgorithm(),
            ImportEnmapL1BAlgorithm(),
            ImportEnmapL1CAlgorithm(),
            ImportEnmapL2AAlgorithm(),
            ImportLandsatL2Algorithm(),
            ImportPrismaL1Algorithm(),
            ImportPrismaL2DAlgorithm(),
            ImportSentinel2L2AAlgorithm()
        ]
        mapLayers = list()
        for alg in algs:
            if alg.isValidFile(filename):
                import enmapbox

                parameters = alg.defaultParameters(filename)
                alreadyExists = True
                for key, value in parameters.items():
                    if key.startswith('output'):
                        alreadyExists &= exists(value)
                if not alreadyExists:
                    enmapBox = enmapbox.EnMAPBox.instance()
                    dialog: AlgorithmDialogWrapper = enmapBox.showProcessingAlgorithmDialog(
                        alg, parameters, True, True, AlgorithmDialogWrapper, False
                    )
                    if not dialog.finishedSuccessful:
                        continue
                    result = dialog.finishResult
                else:
                    result = {key: value for key, value in parameters.items()
                              if key.startswith('output')}

                for key, value in result.items():
                    if parameters[key] is None or value is None:
                        continue
                    layer = QgsRasterLayer(parameters[key], basename(value))
                    mapLayers.append(layer)
        return mapLayers
    except Exception:
        traceback.print_exc()
        return []
