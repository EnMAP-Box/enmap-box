import unittest

from enmapbox import initAll
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects
from qgis.core import QgsProject, edit

start_app()
initAll()


class TestIssue764(EnMAPBoxTestCase):

    def test_SpectralProcessing_RasterMath(self):
        speclib = TestObjects.createSpectralLibrary(2)
        algorithmId = 'enmapbox:RasterMath'.lower()

        parameters = {'code': 'my code input'}

        with edit(speclib):
            SpectralLibraryUtils.addSpectralProfileField(speclib, 'profiles2')
            s = ""
            slw = SpectralLibraryWidget(speclib=speclib)

            spd = SpectralProcessingDialog(speclib=speclib, algorithmId=algorithmId, parameters=parameters)
            # slw.showSpectralProcessingWidget(algorithmId=algorithmId)
            wrapper = spd.processingModelWrapper()

            for k, v in parameters.items():
                w = wrapper.mWrappers[k]
                self.assertEqual(w.value(), v)

            s = ""
            spd.runButton().animateClick(0)

            self.showGui([spd, slw])

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
