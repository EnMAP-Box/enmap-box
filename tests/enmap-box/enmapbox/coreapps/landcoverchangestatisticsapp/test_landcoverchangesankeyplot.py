import numpy as np

from enmapboxprocessing.testcase import TestCase
from enmapboxprocessing.typing import Category
from landcoverchangestatisticsapp.landcoverchangestatisticsmainwindow import LandCoverChangeSankeyPlotBuilder


class TestEnviUtils(TestCase):

    def test_recodeConfusionMatrix(self):
        matrix = np.array(
            [[1, 2, 3, 4, 5],
             [6, 7, 8, 9, 10]]
        )
        categories1 = [Category(i, str(i), '#000000') for i in range(1, 3)]
        categories2 = [Category(i, str(i), '#000000') for i in range(1, 6)]
        filter1 = ['1']
        filter2 = ['1', '3', '5']
        newMatrix, newCategories1, newCategories2 = LandCoverChangeSankeyPlotBuilder.recodeConfusionMatrix(
            matrix, categories1, categories2, filter1, filter2
        )
        self.assertListEqual([[1, 3, 5, 6], [6, 8, 10, 16]], newMatrix.tolist())
        self.assertListEqual(
            [Category(value=1, name='1', color='#000000'), Category(value=-0.1, name='Discarded', color='#ff0000')],
            newCategories1
        )
        self.assertListEqual(
            [Category(value=1, name='1', color='#000000'),
             Category(value=3, name='3', color='#000000'),
             Category(value=5, name='5', color='#000000'),
             Category(value=-0.1, name='Discarded', color='#ff0000')],
            newCategories2
        )

    def test_recodeClassSizes(self):
        values = np.array([1, 2, 3])
        categories = [Category(i, str(i), '#000000') for i in range(1, 4)]
        filter = ['2']
        newValues, newCategories = LandCoverChangeSankeyPlotBuilder().recodeClassSizes(
            values, categories, filter
        )
        print(newValues, newCategories)
