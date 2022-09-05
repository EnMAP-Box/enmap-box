import os
import unittest

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from qgis.core import QgsField, QgsMapLayer
from qgis.core import QgsProject, QgsVectorLayerExporter, QgsVectorLayer
from qgis.gui import QgsEditorWidgetRegistry, QgsGui


class TestIssue724(EnMAPBoxTestCase):

    def tearDown(self):

        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox):
            emb.close()

        assert EnMAPBox.instance() is None

        QgsProject.instance().removeAllMapLayers()

        super().tearDown()

    def test_issue_724(self):

        from enmapbox import registerEditorWidgets
        registerEditorWidgets()
        from enmapbox.qgispluginsupport.qps.speclib.core import EDITOR_WIDGET_REGISTRY_KEY

        # create and save a speclib as GPKG
        sl = TestObjects.createSpectralLibrary()
        self.assertIsInstance(sl, QgsVectorLayer)
        pfieldName = 'profiles0'

        pfield = sl.fields().field(pfieldName)
        self.assertIsInstance(pfield, QgsField)
        self.assertEqual(pfield.editorWidgetSetup().type(), EDITOR_WIDGET_REGISTRY_KEY)

        self.assertTrue(sl.fields().names())
        path = self.createTestOutputDirectory() / 'issue_724' / 'speclib.gpkg'
        os.makedirs(path.parent, exist_ok=True)
        options = dict(overwrite=True)

        result, msg = QgsVectorLayerExporter.exportLayer(sl,
                                                         uri=path.as_posix(),
                                                         providerKey='ogr',
                                                         destCRS=sl.crs(),
                                                         options=options)

        self.assertTrue(result == QgsVectorLayerExporter.NoError, msg=msg)
        lyr = SpectralLibraryUtils.readFromSource(path)
        sl.saveNamedStyle(lyr.styleURI(), QgsMapLayer.StyleCategory.AllStyleCategories)
        msg, success = lyr.loadDefaultStyle()
        self.assertTrue(success, msg=msg)
        del lyr

        filename = path.as_posix()
        reg: QgsEditorWidgetRegistry = QgsGui.editorWidgetRegistry()
        print('Available editor types:')
        for k, v in reg.factories().items():
            print(f'   {k}:"{v.name()}"')

        vl = QgsVectorLayer(filename)
        sl1 = SpectralLibraryUtils.readFromSource(filename)

        slRef = TestObjects.createSpectralLibrary()
        for lyr in [vl, sl1, slRef]:
            self.assertIsInstance(lyr, QgsVectorLayer)
            self.assertTrue(lyr.featureCount() > 0)
            print(f'{lyr.id()}:{lyr.source()}')
            print(f'type: {lyr.fields().field(pfieldName).typeName()}')
            setup = lyr.fields().field(pfieldName).editorWidgetSetup()
            print(f'editor: {setup.type()}')
            print(f'is spectral library?: {is_spectral_library(lyr)}')
            self.assertTrue(setup.type() == EDITOR_WIDGET_REGISTRY_KEY)


if __name__ == '__main__':
    unittest.main(buffer=False)
