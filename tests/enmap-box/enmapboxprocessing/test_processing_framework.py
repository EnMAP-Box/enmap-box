import unittest

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import TestCase, start_app

start_app()
initAll()


class TestProcessingFramework(TestCase):

    @unittest.skipIf(TestCase.runsInCI(), 'Blocking Dialog')
    def test_start_algorithm(self):
        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EMB.loadExampleData()
        EMB.executeAlgorithm('gdal:translate', EMB.ui)
