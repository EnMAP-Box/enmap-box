import unittest

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import TestCase


class TestProcessingFramework(TestCase):

    @unittest.skipIf(TestCase.runsInCI(), 'Blocking Dialog')
    def test_start_algorithm(self):
        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EMB.executeAlgorithm('gdal:translate', EMB.ui)
