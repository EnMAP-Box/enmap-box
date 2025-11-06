import unittest

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import TestCase, start_app
from qgis.core import QgsProject

start_app()
initAll()


class TestProcessingFramework(TestCase):

    @unittest.skipIf(TestCase.runsInCI(), 'Blocking Dialog')
    def test_gdal_translate(self):
        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EMB.loadExampleData()
        EMB.executeAlgorithm('gdal:translate', EMB.ui)
        self.showGui(EMB.ui)
        QgsProject.instance().removeAllMapLayers()

    @unittest.skipIf(TestCase.runsInCI(), 'Blocking Dialog')
    def test_native_virtualrastercalc(self):
        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EMB.loadExampleData()
        EMB.executeAlgorithm('native:virtualrastercalc', EMB.ui)
        self.showGui(EMB.ui)

    @unittest.skipIf(TestCase.runsInCI(), 'Blocking Dialog')
    def test_mask_rasterlayer_virtual(self):
        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EMB.loadExampleData()
        EMB.executeAlgorithm('enmapbox:createmaskrasterlayervirtual', EMB.ui)
        self.showGui(EMB.ui)
        QgsProject.instance().removeAllMapLayers()
