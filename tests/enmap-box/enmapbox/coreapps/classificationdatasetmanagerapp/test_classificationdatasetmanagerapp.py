from classificationdatasetmanagerapp import ClassificationDatasetManagerGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import classifierDumpSkops

qgsApp = start_app()
start_app()


class TestClassificationDatasetManagerApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        enmapBox.addSource(classifierDumpSkops)

        widget = ClassificationDatasetManagerGui(enmapBox.ui)
        widget.show()
        widget.mDataset.mFile.setFilePath(classifierDumpSkops)

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
