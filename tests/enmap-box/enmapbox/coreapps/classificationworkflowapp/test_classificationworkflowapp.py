import os
import unittest

from classificationworkflowapp import ClassificationWorkflowGui
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase

qgsApp = start_app()
start_app()

runs_offscreen = os.environ.get('QT_QPA_PLATFORM', '').lower() in ['offscreen']


@unittest.skipIf(runs_offscreen, 'QT_QPA_PLATFORM=offscreen. QWebEngineView requires a screen device')
class TestClassificationWorkflowApp(TestCase):

    def test_workflowapp(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        widget = ClassificationWorkflowGui()
        widget.show()

        self.showGui([enmapBox.ui, widget])

        enmapBox.close()

        # if False:
        #    qgsApp.exec()

        # self.dispose_widget(widget)
        # self.dispose_widget(enmapBox.ui)
