from enmapboxprocessing.algorithm.classificationfromrenderedimagealgorithm import \
    ClassificationFromRenderedImageAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.utils import Utils
from tests.enmapboxtestdata import landcover_map_l3, enmap_berlin
from qgis.core import QgsMapLayer, QgsSingleBandPseudoColorRenderer, QgsMultiBandColorRenderer, \
    QgsPalettedRasterRenderer, QgsRasterLayer


class TestClassificationFromRenderedImageAlgorithm(TestCase):

    def test_paletted(self):
        layer = QgsRasterLayer(landcover_map_l3)
        self.assertIsInstance(layer.renderer(), QgsPalettedRasterRenderer)
        alg = ClassificationFromRenderedImageAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: landcover_map_l3,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
        }
        self.runalg(alg, parameters)
        layer = QgsRasterLayer(parameters[alg.P_OUTPUT_CLASSIFICATION])
        categories = Utils().categoriesFromRenderer(layer.renderer())
        self.assertListEqual(
            ['#0064ff', '#267300', '#98e600', '#9c9c9c', '#a87000', '#e60000'],
            [c.name for c in categories]
        )
        self.assertListEqual(
            ['#0064ff', '#267300', '#98e600', '#9c9c9c', '#a87000', '#e60000'],
            [c.color for c in categories]
        )

    def test_pseudocolor(self):
        layer = QgsRasterLayer(enmap_berlin)
        qml = enmap_berlin.replace('enmap_berlin.bsq', 'enmap_berlin_pseudocolor.qml')
        layer.loadNamedStyle(qml, QgsMapLayer.StyleCategory.AllStyleCategories)
        self.assertIsInstance(layer.renderer(), QgsSingleBandPseudoColorRenderer)
        alg = ClassificationFromRenderedImageAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: layer,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
        }
        self.runalg(alg, parameters)
        layer = QgsRasterLayer(parameters[alg.P_OUTPUT_CLASSIFICATION])
        categories = Utils().categoriesFromRenderer(layer.renderer())
        self.assertListEqual(
            ['#1a9641', '#a6d96a', '#d7191c', '#fdae61', '#ffffc0'],
            [c.name for c in categories]
        )
        self.assertListEqual(
            ['#1a9641', '#a6d96a', '#d7191c', '#fdae61', '#ffffc0'],
            [c.color for c in categories]
        )

    def test_multiband(self):
        layer = QgsRasterLayer(enmap_berlin)
        self.assertIsInstance(layer.renderer(), QgsMultiBandColorRenderer)
        alg = ClassificationFromRenderedImageAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: layer,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
        }
        self.runalg(alg, parameters)
        layer = QgsRasterLayer(parameters[alg.P_OUTPUT_CLASSIFICATION])
        categories = Utils().categoriesFromRenderer(layer.renderer())
        self.assertEqual(56498, len(categories))
