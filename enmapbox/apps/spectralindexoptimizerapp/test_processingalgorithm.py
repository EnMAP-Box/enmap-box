from os.path import join, dirname

from qgis.core import QgsRasterLayer, QgsRasterLayer, QgsRasterLayer
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing
from spectralindexoptimizerapp.processingalgorithm import SpectralIndexOptimizerProcessingAlgorithm
import enmapboxtestdata

from _classic.hubdc.core import openRasterDataset

# init QGIS
qgsApp = QgsApplication([], True)
qgsApp.initQgis()
qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

# init processing framework
Processing.initialize()

labels = openRasterDataset(filename=enmapboxtestdata.enmap).translate(filename='single.tif', bandList=[1]).filename()

# run algorithm
alg = SpectralIndexOptimizerProcessingAlgorithm()
io = {alg.P_FEATURES: QgsRasterLayer(enmapboxtestdata.enmap),
      alg.P_LABELS: QgsRasterLayer(labels),
      alg.P_INDEX_TYPE: 0, # ndi
      alg.P_PERFORMANCE_TYPE: 0, # RMSE
      alg.P_RASTER: QgsRasterLayer(enmapboxtestdata.enmap),
      alg.P_OUTPUT_PREDICTION: 'prediction.tif',
      alg.P_OUTPUT_REPORT: 'report.html'
      }
result = Processing.runAlgorithm(alg, parameters=io)

print(result)