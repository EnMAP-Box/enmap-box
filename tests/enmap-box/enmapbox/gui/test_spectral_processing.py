import unittest

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import DockTypes, SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.testing import EnMAPBoxTestCase, start_app
from enmapboxtestdata import library_berlin
from qgis.core import QgsVectorLayer

start_app()
initAll()


class TestSpectralProcessing(EnMAPBoxTestCase):

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialog')
    def test_spectralProcessingDialog(self):
        EMB = EnMAPBox(load_core_apps=True, load_other_apps=False)
        # EMB.loadExampleData()
        speclib = QgsVectorLayer(library_berlin, 'Speclib')
        speclib.startEditing()
        SLD: SpectralLibraryDock = EMB.createDock(DockTypes.SpectralLibraryDock, speclib=speclib)
        SLW: SpectralLibraryWidget = SLD.speclibWidget()
        SLW.openSpectralProcessingWidget()
        self.showGui(EMB.ui)
