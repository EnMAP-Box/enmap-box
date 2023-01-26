import unittest

from qgis.core import QgsVectorLayer

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.dataviews.docks import DockTypes, SpectralLibraryDock
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.testing import EnMAPBoxTestCase
from enmapbox.exampledata import library_gpkg


class TestSpectralProcessing(EnMAPBoxTestCase):

    def setUp(self):
        self.closeEnMAPBoxInstance()

    def tearDown(self):
        self.closeEnMAPBoxInstance()

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialog')
    def test_spectralProcessingDialog(self):

        EMB = EnMAPBox(load_core_apps=True, load_other_apps=False)
        # EMB.loadExampleData()
        speclib = QgsVectorLayer(library_gpkg, 'Speclib')
        speclib.startEditing()
        SLD: SpectralLibraryDock = EMB.createDock(DockTypes.SpectralLibraryDock, speclib=speclib)
        SLW: SpectralLibraryWidget = SLD.speclibWidget()
        SLW.showSpectralProcessingWidget()
        self.showGui(EMB.ui)
