from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import regressorDumpSkops
from regressiondatasetmanagerapp import RegressionDatasetManagerGui

qgsApp = start_app()
start_app()


class TestRegressionDatasetManagerGui(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        enmapBox.addSource(regressorDumpSkops)

        widget = RegressionDatasetManagerGui(enmapBox.ui)
        widget.show()
        widget.mDataset.mFile.setFilePath(regressorDumpSkops)

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
