from unittest import TestCase

from enmapbox.exampledata import landcover_polygons
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsVectorLayer


class TestUtils(TestCase):

    def test_(self):
        vector = QgsVectorLayer(landcover_polygons)
        categories = Utils.categoriesFromCategorizedSymbolRenderer(renderer=vector.renderer())
        self.assertListEqual(
            [Category(value='roof', name='roof', color='#e60000'),
             Category(value='pavement', name='pavement', color='#9c9c9c'),
             Category(value='low vegetation', name='low vegetation', color='#98e600'),
             Category(value='tree', name='tree', color='#267300'),
             Category(value='soil', name='soil', color='#a87000'),
             Category(value='water', name='water', color='#0064ff')],
            categories
        )

    def test_parseColor(self):
        white = QColor('#FFFFFF')
        self.assertEqual(white, Utils.parseColor('#FFFFFF'))
        self.assertEqual(white, Utils.parseColor(16777215))
        self.assertEqual(white, Utils.parseColor('16777215'))
        self.assertEqual(white, Utils.parseColor((255, 255, 255)))
        self.assertEqual(white, Utils.parseColor([255, 255, 255]))
        self.assertEqual(white, Utils.parseColor('(255, 255, 255)'))
        self.assertEqual(white, Utils.parseColor('[255, 255, 255]'))
        self.assertEqual(white, Utils.parseColor('255, 255, 255'))

    def test_prepareCategories(self):
        # remove last if empty
        categories, valueLookup = Utils.prepareCategories(
            [Category(42, 'A', '#000000'), Category(0, '', '#000000')],
            removeLastIfEmpty=True
        )
        self.assertEqual([Category(42, 'A', '#000000')], categories)
        self.assertEqual({42: 42}, valueLookup)

        # int to int (nothing should change)
        categories, valueLookup = Utils.prepareCategories([Category(42, 'A', '#000000')])
        self.assertEqual([Category(42, 'A', '#000000')], categories)
        self.assertEqual({42: 42}, valueLookup)

        # decimal-string to int (value is just casted to int)
        categories, valueLookup = Utils.prepareCategories([Category('42', 'A', '#000000')], valuesToInt=True)
        self.assertEqual([Category(42, 'A', '#000000')], categories)
        self.assertEqual({'42': 42}, valueLookup)

        # none-decimal-string to int (value is replaced by category position)
        categories, valueLookup = Utils.prepareCategories([Category('name', 'A', '#000000')], valuesToInt=True)
        self.assertEqual([Category(1, 'A', '#000000')], categories)
        self.assertEqual({'name': 1}, valueLookup)

    def test_wavelengthUnitsConversionFactor(self):
        self.assertEqual(1000, Utils.wavelengthUnitsConversionFactor('m', 'mm'))
