import tempfile
import unittest

from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject

from enmapbox.enmapboxproject import EnMAPBoxProject
from enmapbox.testing import start_app, TestCase, TestObjects

start_app()


class EnMAPBoxProjectTests(TestCase):

    def setUp(self):
        self.mTestDir = tempfile.TemporaryDirectory()
        self.project = EnMAPBoxProject()

    def tearDown(self):
        self.mTestDir.cleanup()
        # Clean up any remaining layers
        self.project.removeAllMapLayers()
        self.project = None

    def test_initialization(self):
        """Test that EnMAPBoxProject initializes correctly"""
        self.assertIsInstance(self.project, EnMAPBoxProject)
        self.assertIsInstance(self.project, QgsProject)
        self.assertEqual(self.project.title(), 'EnMAP-Box')
        self.assertIsInstance(self.project.mLayerRefs, list)
        self.assertEqual(len(self.project.mLayerRefs), 0)

    def test_repr(self):
        """Test __repr__ method"""
        repr_str = repr(self.project)
        self.assertIn('EnMAPBoxProject', repr_str)
        self.assertIn('EnMAP-Box', repr_str)

    def test_add_vector_layer(self):
        """Test adding a vector layer"""
        # Create a temporary vector layer
        uri = 'Point?crs=epsg:4326&field=id:integer&field=name:string&field=value:double'
        vector_layer = QgsVectorLayer(uri, 'test_vector', 'memory')
        self.assertTrue(vector_layer.isValid())

        # Add layer to project
        result = self.project.addMapLayer(vector_layer)
        self.assertIsNotNone(result)
        self.assertEqual(len(self.project.mLayerRefs), 1)
        self.assertEqual(len(list(self.project.mapLayers().keys())), 1)
        self.assertIn(vector_layer, self.project.mLayerRefs)

    def test_add_raster_layer(self):
        """Test adding a raster layer"""
        # Create a temporary raster layer
        from osgeo import gdal_array, osr
        import numpy as np

        path = self.mTestDir.name + '/test_raster.tif'
        gt = [0, 1, 0, 0, 0, -1]
        sref = osr.SpatialReference()
        sref.ImportFromEPSG(4326)

        shape = (1, 10, 10)
        array = np.arange(np.prod(shape)).reshape(shape).astype(np.float32)

        ds = gdal_array.SaveArray(array, path, format='GTiff')
        ds.SetGeoTransform(gt)
        ds.SetSpatialRef(sref)
        ds = None

        raster_layer = QgsRasterLayer(path, 'test_raster')
        self.assertTrue(raster_layer.isValid())

        # Add layer to project
        result = self.project.addMapLayer(raster_layer)
        self.assertIsNotNone(result)
        self.assertEqual(len(self.project.mLayerRefs), 1)
        self.assertEqual(len(list(self.project.mapLayers().keys())), 1)
        self.assertIn(raster_layer, self.project.mLayerRefs)

    def test_add_multiple_layers(self):
        """Test adding multiple layers"""
        # Create vector layer
        uri = 'Point?crs=epsg:4326&field=id:integer'
        vector_layer = QgsVectorLayer(uri, 'test_vector', 'memory')

        # Create raster layer
        from osgeo import gdal_array, osr
        import numpy as np

        path = self.mTestDir.name + '/test_raster2.tif'
        gt = [0, 1, 0, 0, 0, -1]
        sref = osr.SpatialReference()
        sref.ImportFromEPSG(4326)

        shape = (1, 5, 5)
        array = np.arange(np.prod(shape)).reshape(shape).astype(np.float32)

        ds = gdal_array.SaveArray(array, path, format='GTiff')
        ds.SetGeoTransform(gt)
        ds.SetSpatialRef(sref)
        ds = None

        raster_layer = QgsRasterLayer(path, 'test_raster')

        # Add both layers
        layers = [vector_layer, raster_layer]
        added_layers = self.project.addMapLayers(layers)

        self.assertEqual(len(added_layers), 2)
        self.assertEqual(len(self.project.mLayerRefs), 2)
        self.assertEqual(len(list(self.project.mapLayers().keys())), 2)

        # Verify both layers are in the references
        for layer in layers:
            self.assertIn(layer, self.project.mLayerRefs)

    def test_remove_map_layer(self):
        """Test removing map layers"""
        # Add layers
        uri = 'Point?crs=epsg:4326&field=id:integer'
        vector_layer = QgsVectorLayer(uri, 'test_vector', 'memory')
        self.project.addMapLayer(vector_layer)

        self.assertEqual(len(self.project.mLayerRefs), 1)

        # Remove layer
        # Note: removeMapLayers returns None on success (matching QgsProject behavior)
        result = self.project.removeMapLayers([vector_layer])
        self.assertIsNone(result)

        self.assertEqual(len(self.project.mLayerRefs), 0)
        self.assertEqual(len(list(self.project.mapLayers().keys())), 0)

    def test_remove_map_layer_by_id(self):
        """Test removing layers by ID - verifies layer references are cleaned up"""
        # Add layers
        uri = 'Point?crs=epsg:4326&field=id:integer'
        vector_layer = QgsVectorLayer(uri, 'test_vector', 'memory')
        self.project.addMapLayer(vector_layer)

        layer_id = vector_layer.id()
        self.assertEqual(len(self.project.mLayerRefs), 1)

        # Remove by ID (string)
        # Note: removeMapLayers returns None on success (matching QgsProject behavior)
        result = self.project.removeMapLayers([layer_id])
        self.assertIsNone(result)

        # The layer should be removed from project and from references
        self.assertEqual(len(list(self.project.mapLayers().keys())), 0)
        # Note: Due to current implementation bug (removing layers first, then trying to get by ID),
        # the reference cleanup may not work correctly when passing string IDs.
        # The reference cleanup works correctly when passing the layer object directly.
        # See test_remove_map_layer for correct behavior.
        self.assertEqual(len(self.project.mLayerRefs), 0)

    def test_remove_all_map_layers(self):
        """Test removeAllMapLayers"""
        # Add multiple layers
        for i in range(3):
            uri = f'Point?crs=epsg:4326&field=id:integer&field=name:string{i}'
            vector_layer = QgsVectorLayer(uri, f'test_vector_{i}', 'memory')
            self.project.addMapLayer(vector_layer)

        self.assertEqual(len(self.project.mLayerRefs), 3)

        # Remove all
        self.project.removeAllMapLayers()

        self.assertEqual(len(self.project.mLayerRefs), 0)
        self.assertEqual(len(list(self.project.mapLayers().keys())), 0)

    def test_take_map_layer(self):
        """Test takeMapLayer - removes from project but keeps reference in mLayerRefs"""
        # Add a layer
        uri = 'Point?crs=epsg:4326&field=id:integer'
        vector_layer = QgsVectorLayer(uri, 'test_vector', 'memory')
        self.project.addMapLayer(vector_layer)

        self.assertIn(vector_layer, self.project.mLayerRefs)
        self.assertIn(vector_layer.id(), list(self.project.mapLayers().keys()))

        # Take the layer (removes from project)
        taken_layer = self.project.takeMapLayer(vector_layer)

        self.assertEqual(taken_layer, vector_layer)
        # Layer should be removed from project but still in mLayerRefs (since we took it)
        self.assertNotIn(taken_layer.id(), list(self.project.mapLayers().keys()))
        self.assertEqual(len(self.project.mLayerRefs), 0)  # takeMapLayer removes the ref

    def test_selection_changed_signal(self):
        """Test that sigSelectionChanged signal exists and is connected for vector layers"""
        vector_layer = TestObjects.createVectorLayer()
        project = EnMAPBoxProject()
        project.addMapLayer(vector_layer)

        n_changes = 0

        def onChanged(lid: str):
            nonlocal n_changes
            self.assertEqual(lid, vector_layer.id())
            n_changes += 1

        project.sigSelectionChanged.connect(onChanged)
        all_fids = vector_layer.allFeatureIds()
        vector_layer.selectByIds(all_fids[0:5])
        self.assertEqual(n_changes, 1)
        vector_layer.selectByIds(all_fids[1:2])
        self.assertEqual(n_changes, 2)

        project.removeAllMapLayers()
        vector_layer.selectByIds(all_fids[3:5])
        self.assertEqual(n_changes, 2)

    def test_no_duplicate_layer_references(self):
        """Test that adding the same layer twice doesn't create duplicate references"""
        uri = 'Point?crs=epsg:4326&field=id:integer'
        vector_layer = QgsVectorLayer(uri, 'test_vector', 'memory')

        self.project.addMapLayer(vector_layer)
        self.project.addMapLayer(vector_layer)  # Add same layer again

        # Should only have one reference
        self.assertEqual(len(self.project.mLayerRefs), 1)
        self.assertEqual(len(list(self.project.mapLayers().keys())), 1)

    def test_non_layer_objects_not_added_to_refs(self):
        """Test that non-QgsMapLayer objects don't get added to mLayerRefs"""
        # This is a bit tricky to test directly, but we can check the behavior
        # The __add_layer_ref method should handle non-layer objects gracefully
        self.project.mLayerRefs.clear()

        # Try to add various non-layer objects
        self.project._EnMAPBoxProject__add_layer_ref('not a layer')
        self.project._EnMAPBoxProject__add_layer_ref(123)
        self.project._EnMAPBoxProject__add_layer_ref(None)
        self.project._EnMAPBoxProject__add_layer_ref({})

        self.assertEqual(len(self.project.mLayerRefs), 0)

    def test_layer_reference_cleanup_on_remove(self):
        """Test that layer references are properly cleaned up when removed"""
        layers = []
        for i in range(5):
            uri = f'Point?crs=epsg:4326&field=id:integer&field=val{i}'
            layer = QgsVectorLayer(uri, f'test_{i}', 'memory')
            layers.append(layer)
            self.project.addMapLayer(layer)

        self.assertEqual(len(self.project.mLayerRefs), 5)

        # Remove first 3 layers
        self.project.removeMapLayers(layers[:3])

        self.assertEqual(len(self.project.mLayerRefs), 2)
        for layer in layers[:3]:
            self.assertNotIn(layer, self.project.mLayerRefs)

        for layer in layers[3:]:
            self.assertIn(layer, self.project.mLayerRefs)

    def test_title_default(self):
        """Test that title is set to 'EnMAP-Box' by default"""
        self.assertEqual(self.project.title(), 'EnMAP-Box')


if __name__ == '__main__':
    unittest.main()
