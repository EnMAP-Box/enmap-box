import os
import unittest

from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.testing import TestObjects, EnMAPBoxTestCase, start_app
from qgis.core import QgsField, QgsMapLayer
from qgis.core import QgsProject, QgsVectorLayerExporter, QgsVectorLayer
from qgis.gui import QgsEditorWidgetRegistry, QgsGui

start_app()


class TestIssue724(EnMAPBoxTestCase):

    def test_issue_724(self):

        from enmapbox import registerEditorWidgets
        registerEditorWidgets()
        from enmapbox.qgispluginsupport.qps.speclib import EDITOR_WIDGET_REGISTRY_KEY

        # create and save a speclib as GPKG
        sl = TestObjects.createSpectralLibrary(profile_field_names=['p1'])
        self.assertTrue(is_spectral_library(sl))

        test_dir = self.createTestOutputDirectory()
        path = test_dir / 'speclib.gpkg'

        written_files = SpectralLibraryUtils.writeToSource(sl, path.as_posix())

        lyr1 = SpectralLibraryUtils.readFromSource(written_files[0])
        self.assertTrue(is_spectral_library(lyr1))

        lyr2 = QgsVectorLayer(written_files[0].as_posix())
        lyr2.loadDefaultStyle()

        for i, lyr in enumerate([lyr1, lyr2]):
            self.assertTrue(is_spectral_library(lyr), msg=f'Not a speclib: {i} {lyr.source()}')

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
