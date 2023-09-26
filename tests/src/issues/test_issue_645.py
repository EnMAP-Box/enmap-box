from enmapbox import initAll
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapboxprocessing.testcase import TestCase
from qgis.core import QgsVectorLayer
from enmapboxtestdata import library_berlin

class Issue645Tests(TestCase):

    def test_issue_646(self):

        initAll()
        box = EnMAPBox()


        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        dock: SpectralLibraryDock = box.createSpectralLibraryDock(speclib=sl)
        dock.speclibWidget().actionShowSpectralProcessingDialog.trigger()
        self.showGui(box.ui)

    def test_issue_dialog(self):

        initAll()

        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        d = SpectralProcessingDialog(speclib=sl)
        d.setAlgorithm('enmapbox:TranslateRasterLayer')
        self.showGui(d)