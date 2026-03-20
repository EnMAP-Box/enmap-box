import os

import numpy as np
from osgeo import gdal

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import MapDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app, TestCase
from enmapboxprocessing.typing import Category
from enmapboxtestdata import landcover_map_l2
from landcoverchangestatisticsapp import LandCoverChangeStatisticsMainWindow
from landcoverchangestatisticsapp.landcoverchangestatisticsmainwindow import LandCoverChangeSankeyPlotBuilder
from qgis.core import QgsRasterLayer

start_app()
initAll()


class TestLandCoverStatisticsApp(TestCase):

    # def _test(self):
    #
    #     if 0:
    #         # Case with non-matching classes
    #         layers = [QgsRasterLayer(landcover_map_l2, 'landcover_map_l2'),
    #                   QgsRasterLayer(landcover_map_l3, 'landcover_map_l3')]
    #     if 0:
    #         # Case with many classes
    #         layers = [QgsRasterLayer(r'D:\data\CORINE\U2000_CLC1990_V2020_20u1.tif', '1990'),
    #                   QgsRasterLayer(r'D:\data\CORINE\U2006_CLC2000_V2020_20u1.tif', '2006'),
    #                   QgsRasterLayer(r'D:\data\CORINE\U2018_CLC2018_V2020_20u1.tif', '2018')]
    #     if 0:
    #         # Case with many maps
    #         layers = [QgsRasterLayer(rf'D:\data\timeseries\MAP_BLCM_{i}.tif', str(i)) for i in
    #                   range(2014, 2017)]  # 2021)]
    #
    #     if 1:
    #         layers = [QgsRasterLayer(landcover_map_l2, 'Level 2'), QgsRasterLayer(landcover_map_l3, 'Level 3')]
    #
    #     builder = LandCoverChangeSankeyPlotBuilder()
    #     builder.setOptions()
    #     builder.setGrid(layers[0])
    #     builder.setLayers(layers)
    #     builder.setClassFilter(classFilter)
    #     builder.readData(layers[0].extent(), 250000)
    #     fig = builder.sankeyPlot()
    #     fig.show()

    def test_LandCoverChangeStatisticsMainWindow(self):
        tmp_dir = self.createTestOutputDirectory()
        path_lc2 = str(tmp_dir / 'changed_landcover.tif')
        if not os.path.isfile(path_lc2):
            ds1: gdal.Dataset = gdal.Open(str(landcover_map_l2))
            band1 = ds1.GetRasterBand(1)
            cnames = band1.GetCategoryNames()
            ccolors = band1.GetColorTable()
            data: np.ndarray = band1.ReadAsArray().flatten()
            n_total = len(data)
            n_to_change = max(1, int(n_total * 0.25))
            indices_to_change = np.random.choice(n_total, size=n_to_change, replace=False)
            data[indices_to_change] = data[0:n_to_change]
            data = data.reshape(ds1.RasterYSize, ds1.RasterXSize)
            from osgeo import gdal_array
            ds2: gdal.Dataset = gdal_array.SaveArray(data, path_lc2, prototype=ds1)
            band2: gdal.Band = ds2.GetRasterBand(1)
            band2.SetCategoryNames(cnames)
            band2.SetColorTable(ccolors)
            ds2.FlushCache()
            del band2, ds2, band1, ds1

        l1 = QgsRasterLayer(landcover_map_l2, 'cover1')
        l2 = QgsRasterLayer(path_lc2, 'cover2')
        l2.setRenderer(l1.renderer().clone())

        emb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        layers = [l1, l2]
        dock: MapDock = emb.createMapDock('MAP')
        dock.addLayers(layers)

        widget = LandCoverChangeStatisticsMainWindow()
        widget.show()
        widget.mSettingsDock.mLayers.setCurrentLayers(layers)
        widget.onLayersChanged()

        self.showGui(widget)
        emb.close()

    def test_LandCoverChangeStatisticsMainWindow_2(self):
        l1 = QgsRasterLayer(landcover_map_l2, 'landcover_map_l2')
        l2 = QgsRasterLayer(landcover_map_l2, 'landcover_map_l2')
        emb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        layers = [l1, l2]
        dock: MapDock = emb.createMapDock('MAP')
        dock.addLayers(layers)

        widget = LandCoverChangeStatisticsMainWindow()
        widget.show()
        widget.mSettingsDock.mLayers.setCurrentLayers(layers)
        widget.onLayersChanged()

        self.showGui(widget)
        emb.close()

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
