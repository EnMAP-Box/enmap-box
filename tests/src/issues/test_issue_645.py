import gc

from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QDialog

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog, \
    SpectralProcessingRasterLayerWidgetWrapper
from enmapboxprocessing.parameter.processingparametercreationprofilewidget import \
    ProcessingParameterCreationProfileWidgetWrapper
from enmapboxprocessing.testcase import TestCase
from processing import AlgorithmDialog
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.wrappers import WidgetWrapperFactory, WidgetWrapper
from qgis._core import QgsProcessingContext, QgsProject, QgsProcessingRegistry, QgsApplication, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer, QgsProcessingParameterDefinition
from qgis._gui import QgsProcessingAlgorithmDialogBase, QgsProcessingGui, QgsGui, \
    QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetContext, QgsProcessingContextGenerator
from qgis.core import QgsVectorLayer
from enmapboxtestdata import library_berlin
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingModelCreatorAlgorithmWrapper

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

    def test_wrappers(self):

        a0 = 'gdal:translate'
        a1 = 'enmapbox:SpectralResamplingToWavelength'
        a2 = 'enmapbox:TranslateRasterLayer'
        parent = QDialog()
        # a = 'gdal:translate'
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        for a in [a0, a1, a2]:
            alg: QgsProcessingAlgorithm = reg.algorithmById(a)
            print(f'Test {alg.id()}')
            for param in alg.parameterDefinitions():
                label1 = label2 = None
                param: QgsProcessingParameterDefinition
                print(f'\t{param.name()}')
                wrapper = WidgetWrapperFactory.create_wrapper(param, parent, row=0, col=0)

                if isinstance(wrapper, WidgetWrapper):

                    label1 = wrapper.wrappedLabel()

                    if label1 is None:
                        label1 = wrapper.createWrappedLabel()
                    if isinstance(wrapper, WidgetWrapper):
                        s = ""
                    else:
                        s = ""
                    if label1:
                        assert isinstance(label1, QLabel)

                        label2 = wrapper.wrappedLabel()
                        assert label1 == label2


        # self.assertEqual(id(label1), id(label2))


        s = ""
    def test_wrapper(self):

        initAll()
        a = 'enmapbox:TranslateRasterLayer'
        # a = 'enmapbox:SpectralResamplingToWavelength'

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

        p.setLayout(QHBoxLayout())
        p.layout().addWidget(w)
        self.showGui(p)


class TestBase(QgsProcessingAlgorithmDialogBase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
