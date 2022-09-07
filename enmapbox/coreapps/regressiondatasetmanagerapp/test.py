from enmapbox import EnMAPBox
from enmapbox.testing import initQgisApplication
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import regressorDumpMultiTargetPkl
from regressiondatasetmanagerapp import RegressionDatasetManagerGui

qgsApp = initQgisApplication()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.pickleDump(Utils.pickleLoad(regressorDumpMultiTargetPkl), 'regressor.pkl')
enmapBox.addSource('regressor.pkl')

widget = RegressionDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec_()
