import unittest

import numpy as np

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibraryrasterdataprovider import \
    createRasterLayers
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapbox.qgispluginsupport.qps.utils import rasterArray
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
from enmapboxprocessing.parameter.processingparameterrastermathcodeeditwidget import \
    ProcessingParameterRasterMathCodeEditWidgetWrapper, ProcessingParameterRasterMathCodeEdit
from processing import AlgorithmDialog
from qgis._core import QgsProcessingContext
from qgis.core import QgsProject, edit, QgsProcessingParameterString, QgsRasterLayer
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetContext

start_app()


class TestIssue764(EnMAPBoxTestCase):

    def test_SpectralProcessing_RasterMath(self):
        initAll()

        speclib = TestObjects.createSpectralLibrary(2)
        algorithmId = 'enmapbox:RasterMath'

        parameters = {'code': 'my code input'}

        with edit(speclib):
            SpectralLibraryUtils.addSpectralProfileField(speclib, 'profiles2')
            s = ""
            slw = SpectralLibraryWidget(speclib=speclib)

            spd = SpectralProcessingDialog(speclib=speclib, algorithmId=algorithmId, parameters=parameters)
            slw.showSpectralProcessingWidget(algorithmId=algorithmId)
            wrapper = spd.processingModelWrapper()

            for k, v in parameters.items():
                w = wrapper.mWrappers[k]
                self.assertEqual(w.value(), v)

            s = ""
            self.showGui([spd, slw])

        QgsProject.instance().removeAllMapLayers()

    def test_RasterMathWidgets(self):

        alg = RasterMathAlgorithm()
        alg.initAlgorithm({})
        p = alg.parameterDefinition(RasterMathAlgorithm.P_CODE)

        self.assertIsInstance(p, QgsProcessingParameterString)
        algDialog = AlgorithmDialog(alg)
        wrapper = ProcessingParameterRasterMathCodeEditWidgetWrapper(p, algDialog)
        self.assertIsInstance(wrapper, QgsAbstractProcessingParameterWidgetWrapper)

        speclib = TestObjects.createSpectralLibrary()

        # create a QgsRasterLayer for Spectral Library vector attributes
        # using the VectorLayerFieldRasterDataProvider(QgsRasterDataProvider)
        # this way we do not need to write extra "files" just to parameterize widgets
        layers = createRasterLayers(speclib)
        # add another raster layer -> uses the GDAL backend
        layers.append(TestObjects.createRasterLayer(path='/vsimem/mytif.tif'))

        for lyr in layers:
            self.assertIsInstance(lyr, QgsRasterLayer)
            self.assertTrue(lyr.isValid())
            data = rasterArray(lyr)
            self.assertIsInstance(data, np.ndarray)

        project = QgsProject()
        project.addMapLayers(layers)

        processingContext = QgsProcessingContext()
        processingContext.setProject(project)

        widgetContext = QgsProcessingParameterWidgetContext()
        widgetContext.setProject(project)

        wrapper.setWidgetContext(widgetContext)
        if True:
            # show the ProcessingParameterRasterMathCodeEdit widget only
            if True:
                # old way
                widget = wrapper.widget
                widget: ProcessingParameterRasterMathCodeEdit
                layers_in_widget = widget.getRasterSources()

                for lyr in project.mapLayers().values():
                    if isinstance(lyr, QgsRasterLayer):
                        pass
                        #self.assertTrue(lyr.id() in layers_in_widget.values(),
                        #                msg=f'{lyr} not shown in ProcessingParameterRasterMathCodeEdit')
            else:
                # new way: proper provider
                widget = wrapper.createWrappedWidget(processingContext)
            self.showGui(widget)
        else:
            # show standard AlgorithmDialog, which uses a standard processing context (QgsProject.instance())
            self.showGui(algDialog)



if __name__ == '__main__':
    unittest.main(buffer=False)
