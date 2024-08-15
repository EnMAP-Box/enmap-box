import numpy as np

from enmapboxprocessing.testcase import TestCase
from enmapboxprocessing.typing import Category
from enmapboxtestdata import landcover_map_l2, landcover_map_l3
from landcoverchangestatisticsapp.landcoverchangestatisticsmainwindow import LandCoverChangeSankeyPlotBuilder
from qgis.core import QgsRasterLayer


class TestEnviUtils(TestCase):

    def _test(self):

        if 0:
            # Case with non-matching classes
            layers = [QgsRasterLayer(landcover_map_l2, 'landcover_map_l2'),
                      QgsRasterLayer(landcover_map_l3, 'landcover_map_l3')]
        if 0:
            # Case with many classes
            layers = [QgsRasterLayer(r'D:\data\CORINE\U2000_CLC1990_V2020_20u1.tif', '1990'),
                      QgsRasterLayer(r'D:\data\CORINE\U2006_CLC2000_V2020_20u1.tif', '2006'),
                      QgsRasterLayer(r'D:\data\CORINE\U2018_CLC2018_V2020_20u1.tif', '2018')]
        if 0:
            # Case with many maps
            layers = [QgsRasterLayer(rf'D:\data\timeseries\MAP_BLCM_{i}.tif', str(i)) for i in
                      range(2014, 2017)]  # 2021)]

        if 1:
            layers = [QgsRasterLayer(landcover_map_l2, 'Level 2'), QgsRasterLayer(landcover_map_l3, 'Level 3')]

        builder = LandCoverChangeSankeyPlotBuilder()
        builder.setOptions()
        builder.setGrid(layers[0])
        builder.setLayers(layers)
        builder.setClassFilter(classFilter)
        builder.readData(layers[0].extent(), 250000)
        fig = builder.sankeyPlot()
        fig.show()

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
            [Category(value=1, name='1', color='#000000'), Category(value=-0.1, name='Rest', color='#ff0000')],
            newCategories1
        )
        self.assertListEqual(
            [Category(value=1, name='1', color='#000000'),
             Category(value=3, name='3', color='#000000'),
             Category(value=5, name='5', color='#000000'),
             Category(value=-0.1, name='Rest', color='#ff0000')],
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
