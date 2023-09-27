from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog, \
    SpectralProcessingRasterLayerWidgetWrapper
from enmapboxprocessing.testcase import TestCase
from processing import AlgorithmDialog
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.wrappers import WidgetWrapperFactory
from qgis._core import QgsProcessingContext, QgsProject, QgsProcessingRegistry, QgsApplication, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer
from qgis._gui import QgsProcessingAlgorithmDialogBase, QgsProcessingGui, QgsGui, \
    QgsAbstractProcessingParameterWidgetWrapper
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

    def test_wrapper(self):

        initAll()
        base = TestBase()
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


        if True:
            w = SpectralProcessingModelCreatorAlgorithmWrapper(alg, sl, context, parent=p)
            # w.initWidgets()
            p.setLayout(QHBoxLayout())
            p.layout().addWidget(w)
            self.showGui(p)

        else:

            p2 = QWidget()
            grid = QGridLayout()
            p2.setLayout(grid)
            # 'createProfile'
            wrappers = []
            for r, param in enumerate(alg.parameterDefinitions()):
                # print(f'{r+1} {param.name()}')
                wrapper = None
                if isinstance(param, QgsProcessingParameterRasterLayer):
                    # workaround https://github.com/qgis/QGIS/issues/46673
                    wrapper = SpectralProcessingRasterLayerWidgetWrapper(param, QgsProcessingGui.Standard)
                else:
                    # todo: remove for QGSI 4.0
                    wrapper_metadata = param.metadata().get('widget_wrapper', None)
                    # VERY messy logic here to avoid breaking 3.0 API which allowed metadata "widget_wrapper" value to be either
                    # a string name of a class OR a dict.
                    # TODO QGIS 4.0 -- require widget_wrapper to be a dict.
                    if wrapper_metadata and (
                            not isinstance(wrapper_metadata, dict) or wrapper_metadata.get('class', None) is not None):
                        wrapper = WidgetWrapperFactory.create_wrapper_from_metadata(param, p2, row=0, col=0)
                    else:
                        wrapper = QgsGui.processingGuiRegistry().createParameterWidgetWrapper(param,
                                                                                              QgsProcessingGui.Standard)

                assert isinstance(wrapper, QgsAbstractProcessingParameterWidgetWrapper)

                if wrapper:
                    print(f'{r} {param.name()} {wrapper.__class__.__name__}')
                    wrappers.append(wrapper)
                    label = wrapper.createWrappedLabel()
                    widget = wrapper.createWrappedWidget(context)
                    wrappers.extend([label, widget])
                    grid.addWidget(QLabel(f'param {r}'), r, 0)
                    grid.addWidget(wrapper.wrappedLabel(), r , 1, )
                    grid.addWidget(wrapper.wrappedWidget(), r, 2, )
                    s = ""
            self.showGui(p2)


class TestBase(QgsProcessingAlgorithmDialogBase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
