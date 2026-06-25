from regressiondatasetmanagerapp import RegressionDatasetManagerGui

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.utils import Utils
from tests.enmapboxtestdata import regressorDumpMultiTargetSkops

qgsApp = start_app()
enmapBox = EnMAPBox()
enmapBox.run()

Utils.modelDump(Utils.modelLoad(regressorDumpMultiTargetSkops), 'regressor.skops')
enmapBox.addSource('regressor.skops')

widget = RegressionDatasetManagerGui(enmapBox.ui)
widget.show()

qgsApp.exec()
