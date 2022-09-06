from collections import OrderedDict
from os.path import join, dirname
from unittest import TestCase

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRasterLayer, QgsPalettedRasterRenderer, QgsSingleBandGrayRenderer

import numpy as np

from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.raster import Raster


class TestCategory(TestCase):

    def test_fromQgsPalettedRasterRenderer(self):
        filename = '/vsimem/classification.bsq'
        classification = Raster.createFromArray(array=np.array([[[0, 1, 2, 3]]]), filename=filename)
        del classification
        qgsRasterLayer = QgsRasterLayer(filename)
        classes = [
            QgsPalettedRasterRenderer.Class(value=1, color=QColor(255, 0, 0), label='C1'),
            QgsPalettedRasterRenderer.Class(value=3, color=QColor(0, 255, 0), label='C2'),
        ]
        renderer = QgsPalettedRasterRenderer(input=qgsRasterLayer.dataProvider(), bandNumber=1, classes=classes)
        qgsRasterLayer.setRenderer(renderer=renderer)
        assert isinstance(qgsRasterLayer.renderer(), QgsPalettedRasterRenderer)

        categories = Category.fromQgsPalettedRasterRenderer(renderer=qgsRasterLayer.renderer())
        gold = [
            Category(id=1, name='C1', color=Color(red=255, green=0, blue=0, alpha=255)),
            Category(id=3, name='C2', color=Color(red=0, green=255, blue=0, alpha=255))
        ]
        self.assertEqual(categories, gold)
