from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.utils import Utils
from tests.enmapboxtestdata import regressorDumpMultiTargetSkops
from regressiondatasetmanagerapp import RegressionDatasetManagerGui

qgsApp = start_app()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.modelDump(Utils.modelLoad(regressorDumpMultiTargetSkops), 'regressor.skops')
enmapBox.addSource('regressor.skops')

widget = RegressionDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec_()
