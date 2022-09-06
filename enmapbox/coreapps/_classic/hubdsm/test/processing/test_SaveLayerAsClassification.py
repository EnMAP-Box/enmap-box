from collections import OrderedDict
from os.path import join, dirname

import numpy as np
from qgis.core import QgsRasterLayer, QgsVectorLayer

from enmapbox.exampledata import landcover_points, enmap
from _classic.hubdsm.algorithm.uniquebandvaluecounts import uniqueBandValueCounts
from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.processing.savelayerasclassification import SaveLayerAsClassification
from _classic.hubdsm.test.processing.testcase import TestCase


class TestSaveLayerAsClassification(TestCase):

    def test_raster(self):
        filename = '/vsimem/raster.bsq'
        array = np.array([[[0, 10, 20]]])
        raster = Raster.createFromArray(array=array, filename=filename)
        categories = [
            Category(id=10, name='a', color=Color(255, 0, 0)),
            Category(id=20, name='b', color=Color(0, 0, 255))
        ]
        raster.setCategories(categories=categories)
        del raster

        alg = SaveLayerAsClassification()
        io = {
            alg.P_MAP: QgsRasterLayer(filename),
            alg.P_GRID: None,
            alg.P_OUTRASTER: 'c:/vsimem/classification.vrt'
        }
        result = self.runalg(alg=alg, io=io)

        classification = Raster.open(result[alg.P_OUTRASTER])
        self.assertSequenceEqual(classification.categories, categories)
        self.assertTrue(np.all(np.equal(classification.readAsArray(), array)))

    def test_vectorCategorizedById(self):
        qgsVectorLayer = QgsVectorLayer(landcover_points)
        qgsVectorLayer.loadNamedStyle(join(dirname(__file__), 'landcover_berlin_point_categorizedById.qml'))
        self.assertEqual(qgsVectorLayer.renderer().classAttribute(), 'level_2_id')
        alg = SaveLayerAsClassification()
        io = {
            alg.P_MAP: qgsVectorLayer,
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTRASTER: '/vsimem/classification.bsq'
        }
        result = self.runalg(alg=alg, io=io)

        categories = [
            Category(id=1, name='impervious', color=Color(red=230, green=0, blue=0, alpha=255)),
            Category(id=2, name='low vegetation', color=Color(red=152, green=230, blue=0, alpha=255)),
            Category(id=3, name='tree', color=Color(red=38, green=115, blue=0, alpha=255)),
            Category(id=4, name='soil', color=Color(red=168, green=112, blue=0, alpha=255)),
            Category(id=5, name='water', color=Color(red=0, green=100, blue=255, alpha=255)),
            Category(id=6, name='', color=Color(red=255, green=255, blue=255, alpha=255))
        ]
        counts = OrderedDict([(0, 87942), (1, 19), (2, 11), (3, 10), (4, 9), (5, 9)])

        classification = Raster.open(result[alg.P_OUTRASTER])
        print(classification.categories)
        self.assertListEqual(classification.categories, categories)
        self.assertDictEqual(uniqueBandValueCounts(band=classification.band(1)), counts)

    def test_vectorCategorizedByName(self):
        qgsVectorLayer = QgsVectorLayer(landcover_points)
        qgsVectorLayer.loadNamedStyle(join(dirname(__file__), 'landcover_berlin_point_categorizedByName.qml'))
        self.assertEqual(qgsVectorLayer.renderer().classAttribute(), 'level_2')
        alg = SaveLayerAsClassification()
        io = {
            alg.P_MAP: qgsVectorLayer,
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTRASTER: '/vsimem/classification.bsq'
        }
        result = self.runalg(alg=alg, io=io)

        categories = [
            Category(id=1, name='impervious', color=Color(red=230, green=0, blue=0, alpha=255)),
            Category(id=2, name='low vegetation', color=Color(red=152, green=230, blue=0, alpha=255)),
            Category(id=3, name='tree', color=Color(red=38, green=115, blue=0, alpha=255)),
            Category(id=4, name='soil', color=Color(red=168, green=112, blue=0, alpha=255)),
            Category(id=5, name='water', color=Color(red=0, green=100, blue=255, alpha=255)),
            Category(id=6, name='', color=Color(red=255, green=255, blue=255, alpha=255))
        ]
        counts = OrderedDict([(0, 87942), (1, 19), (2, 11), (3, 10), (4, 9), (5, 9)])

        classification = Raster.open(result[alg.P_OUTRASTER])
        self.assertListEqual(classification.categories, categories)
        self.assertDictEqual(uniqueBandValueCounts(band=classification.band(1)), counts)

    def test_vector2(self):
        filename = 'C:/source/QGISPlugIns/enmap-box/enmapboxtestdata/landcover_berlin_polygon.shp'
        filenameGrid = 'C:/source/QGISPlugIns/enmap-box/enmapboxtestdata/hires_berlin.bsq'
        alg = SaveLayerAsClassification()
        io = {
            alg.P_MAP: QgsVectorLayer(filename),
            alg.P_GRID: QgsRasterLayer(filenameGrid),
            alg.P_OUTRASTER: 'c:/vsimem/classification.bsq'
        }
        result = self.runalg(alg=alg, io=io)

        classification = Raster.open(result[alg.P_OUTRASTER])
        print(classification)
        print(classification.categories)
