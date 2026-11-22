from classificationdatasetmanagerapp import ClassificationDatasetManagerGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import classifierDumpSkops

qgsApp = start_app()
start_app()


class TestClassificationDatasetManagerApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        enmapBox.addSource(classifierDumpSkops)

        widget = ClassificationDatasetManagerGui(enmapBox.ui)
        widget.show()
        widget.mDataset.mFile.setFilePath(classifierDumpSkops)

        self.showGui([enmapBox.ui, widget])

        enmapBox.close()
