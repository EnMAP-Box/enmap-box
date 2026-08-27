from classificationworkflowapp import ClassificationWorkflowGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase

qgsApp = start_app()
start_app()


class TestClassificationWorkflowApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()

        widget = ClassificationWorkflowGui()
        widget.show()

        self.showGui([enmapBox.ui, widget])

        # if False:
        #    qgsApp.exec()

        # self.dispose_widget(widget)
        # self.dispose_widget(enmapBox.ui)
