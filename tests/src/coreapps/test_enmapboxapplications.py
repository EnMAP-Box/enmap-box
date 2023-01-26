import pathlib
import site
import unittest

from enmapbox import DIR_ENMAPBOX
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.core import profile_field_list
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibraryrasterdataprovider import registerDataProvider
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import SpectralSetting
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from qgis.PyQt.QtWidgets import QDialogButtonBox
from qgis.core import QgsApplication
from qgis.core import QgsVectorLayer, QgsProcessingRegistry, QgsProcessingAlgorithm

site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'coreapps')
site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'eo4qapps')


class TestEnMAPBoxApplications(EnMAPBoxTestCase):

    def test_createtestdata(self):
        EB: EnMAPBox = EnMAPBox.instance()
        if not isinstance(EB, EnMAPBox):
            EB = EnMAPBox()
            EB.initEnMAPBoxApplications()
        all_ids = [a.id() for a in QgsApplication.processingRegistry().algorithms()]

        test_algs = [a for a in all_ids if a.startswith('enmapbox:CreateTest')]

        from processing.gui.AlgorithmDialog import AlgorithmDialog
        import time
        for a in test_algs:
            n_before = len(EB.dataSources())
            d = EB.showProcessingAlgorithmDialog(a)
            self.assertIsInstance(d, AlgorithmDialog)
            d.buttonBox().button(QDialogButtonBox.Ok).click()
            time.sleep(2)
            while QgsApplication.taskManager().countActiveTasks() > 0:
                QgsApplication.processEvents()
            QgsApplication.processEvents()
            time.sleep(2)

            n_produced = len(EB.dataSources()) - n_before
            d.buttonBox().button(QDialogButtonBox.Close).click()
            self.assertTrue(n_produced > 0, msg='Algorithm "{}" did not create any data source'.format(a.id()))

        self.showGui(EB.ui)

    def test_UiLibrary(self):
        # Addresses https://bitbucket.org/hu-geomatics/enmap-box/issues/310/attributeerror-function-object-has-no

        enmapBox = EnMAPBox(load_core_apps=True, load_other_apps=False)
        enmapBox.loadExampleData()
        self.assertIsInstance(enmapBox, EnMAPBox)

        # how to get SPECLIBs listed in the EnMAP-Box
        # a) get the URI
        speclibUris = enmapBox.dataSources('SPECLIB')

        speclibDataSources = enmapBox.dataSourceManager().sources('SPECLIB')

        self.assertTrue(len(speclibUris) > 0)
        self.assertEqual(len(speclibUris), len(speclibDataSources))

        from enmapboxapplications.widgets.core import UiLibrary
        speclibCB = UiLibrary()

        self.assertTrue(len(speclibDataSources) == speclibCB.count() - 1)

    def test_Resampling(self):
        registerDataProvider()
        n_bands = [256, 13]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer

        slw = SpectralLibraryWidget(speclib=speclib)
        pFields = profile_field_list(speclib)

        speclib.startEditing()
        procw = SpectralProcessingDialog()
        procw.setSpeclib(speclib)
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        alg = reg.algorithmById('enmapbox:SpectralResamplingToLandsat89Oli')
        self.assertIsInstance(alg, QgsProcessingAlgorithm)
        procw.setAlgorithm(alg)
        wrapper = procw.processingModelWrapper()
        cbInputField = wrapper.parameterWidget('raster')
        cbInputField.setCurrentIndex(1)
        currentInputFieldName = cbInputField.currentText()

        cb2 = wrapper.outputWidget('outputResampledRaster')
        cb2.setCurrentText('newfield')

        procw.runAlgorithm(fail_fast=True)
        tempFiles = procw.temporaryRaster()
        for file in tempFiles:
            setting = SpectralSetting.fromRasterLayer(file)
            assert setting.xUnit() not in [None, '']

        self.showGui([slw, procw])


if __name__ == "__main__":
    unittest.main(buffer=False)
