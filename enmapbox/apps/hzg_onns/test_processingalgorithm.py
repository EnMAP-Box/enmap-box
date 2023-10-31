from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing
from hzg_onns.processingalgorithm import OnnsProcessingAlgorithm
from tests import enmapboxtestdata

# init QGIS
qgsApp = QgsApplication([], True)
qgsApp.initQgis()
qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

# init processing framework
Processing.initialize()

# run algorithm
alg = OnnsProcessingAlgorithm()
io = {alg.P_FILE: r'C:\source\onns_for_enmap-box\hzg_onns_testdata\S3A_OL_2_WFRC8R_20160720T093421_20160720T093621_20171002T063739_0119_006_307______MR1_R_NT_002_sylt.nc',
      alg.P_OUTPUT_FOLDER: r'C:\_test_onns'}

result = Processing.runAlgorithm(alg, parameters=io)

print(result)
