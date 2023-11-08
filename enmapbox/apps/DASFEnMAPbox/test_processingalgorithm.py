import os
import warnings
from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing
from DASFEnMAPbox.processingalgorithm import DASFretrievalAlgorithm

import enmapboxtestdata

# init QGIS
qgsApp = QgsApplication([], True)
qgsApp.initQgis()
qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

# init processing framework
Processing.initialize()

path = r"C:\Users\Marion\Desktop\EnMAP_box\MyTool\KROOF03_Viertel_RFC_geo_1m_subset710_790.bsq"
# run algorithm
if not os.path.isfile(path):
    warnings.warn(f'File does not exist: {path}\n skip DASF tests')
else:
    alg = DASFretrievalAlgorithm()
    io = {alg.P_INPUT: path,
          alg.P_OUTPUT: join(dirname(__file__), 'DASF.bsq'),
          alg.P_Retrieval_Quality: join(dirname(__file__), 'DASF_retrievalQuality.bsq'),
          alg.P_CSC: join(dirname(__file__), 'CSC.bsq')}
    result = Processing.runAlgorithm(alg, parameters=io)

    print(result)

    if True: # show the result in a viewer
        from _classic.hubdc.core import MapViewer, openRasterDataset
        fraction = openRasterDataset(result[alg.P_OUTPUT])
        MapViewer().addLayer(fraction.mapLayer().initMultiBandColorRenderer(0, 2, 4, percent=0)).show()
