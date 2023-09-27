from PyQt5.QtWidgets import QWidget

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapboxprocessing.testcase import TestCase
from processing.gui.wrappers import WidgetWrapperFactory
from qgis._core import QgsProcessingContext, QgsProject, QgsProcessingRegistry, QgsApplication, QgsProcessingAlgorithm
from qgis._gui import QgsProcessingAlgorithmDialogBase
from qgis.core import QgsVectorLayer
from enmapboxtestdata import library_berlin
from qps.speclib.gui.spectralprocessingdialog import SpectralProcessingModelCreatorAlgorithmWrapper


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

    def test_wrapper(self):

        initAll()
        base = TestBase()
        a = 'enmapbox:TranslateRasterLayer'
        # a = 'gdal:translate'
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        alg: QgsProcessingAlgorithm = reg.algorithmById(a)
        self.assertIsInstance(alg, QgsProcessingAlgorithm)
        sl = QgsVectorLayer(library_berlin)
        sl.startEditing()
        context = QgsProcessingContext()
        project = QgsProject()
        context.setProject(project)
        p = QWidget()
        w = SpectralProcessingModelCreatorAlgorithmWrapper(alg, sl, context, parent=p)
        w.initWidgets()
        self.showGui(w)

        p2 = QWidget()
        # 'createProfile'
        for param in alg.parameterDefinitions():
            if param.name() == 'createProfile':
                wrapper = WidgetWrapperFactory.create_wrapper_from_metadata(param, p2, row=0, col=0)
                s = ""
        self.showGui(p)


class TestBase(QgsProcessingAlgorithmDialogBase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
