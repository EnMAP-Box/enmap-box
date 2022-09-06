from os.path import join, dirname
from unittest import TestCase

from qgis.core import QgsVectorLayer

from enmapbox.exampledata import landcover_points
from _classic.hubdsm.core.qgsvectorclassificationscheme import QgsVectorClassificationScheme


class TestQgsVectorClassificationScheme(TestCase):

    def test_fromQgsVectorLayer(self):
        qgsVectorLayer = QgsVectorLayer(landcover_points)
        qgsVectorLayer.loadNamedStyle(join(dirname(__file__), 'landcover_berlin_point_categorizedById.qml'))
        qgsVectorClassificationScheme = QgsVectorClassificationScheme.fromQgsVectorLayer(qgsVectorLayer=qgsVectorLayer)
        self.assertEqual(
            str(qgsVectorClassificationScheme),
            "QgsVectorClassificationScheme(categories=OrderedDict([(1, Category(id=1, name='impervious', color=Color(red=230, green=0, blue=0, alpha=255))), (2, Category(id=2, name='low vegetation', color=Color(red=152, green=230, blue=0, alpha=255))), (3, Category(id=3, name='tree', color=Color(red=38, green=115, blue=0, alpha=255))), (4, Category(id=4, name='soil', color=Color(red=168, green=112, blue=0, alpha=255))), (5, Category(id=5, name='water', color=Color(red=0, green=100, blue=255, alpha=255))), ('', Category(id=6, name='', color=Color(red=255, green=255, blue=255, alpha=255)))]), classAttribute='level_2_id')"
        )
        qgsVectorLayer.loadNamedStyle(join(dirname(__file__), 'landcover_berlin_point_categorizedByName.qml'))
        qgsVectorClassificationScheme = QgsVectorClassificationScheme.fromQgsVectorLayer(qgsVectorLayer=qgsVectorLayer)
        self.assertEqual(
            str(qgsVectorClassificationScheme),
            "QgsVectorClassificationScheme(categories=OrderedDict([('impervious', Category(id=1, name='impervious', color=Color(red=230, green=0, blue=0, alpha=255))), ('low vegetation', Category(id=2, name='low vegetation', color=Color(red=152, green=230, blue=0, alpha=255))), ('tree', Category(id=3, name='tree', color=Color(red=38, green=115, blue=0, alpha=255))), ('soil', Category(id=4, name='soil', color=Color(red=168, green=112, blue=0, alpha=255))), ('water', Category(id=5, name='water', color=Color(red=0, green=100, blue=255, alpha=255))), ('', Category(id=6, name='', color=Color(red=255, green=255, blue=255, alpha=255)))]), classAttribute='level_2')"
        )
