from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import regressorDumpMultiTargetPkl
from regressiondatasetmanagerapp import RegressionDatasetManagerGui

qgsApp = start_app()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.pickleDump(Utils.pickleLoad(regressorDumpMultiTargetPkl), 'regressor.pkl')
enmapBox.addSource('regressor.pkl')

widget = RegressionDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec_()
