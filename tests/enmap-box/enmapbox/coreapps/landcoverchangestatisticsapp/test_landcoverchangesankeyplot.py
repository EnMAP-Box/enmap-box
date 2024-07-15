from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import landcover_map_l2, landcover_map_l3
from landcoverchangestatisticsapp.landcoverchangestatisticsdialog import LandCoverChangeSankeyPlotBuilder
from qgis.core import QgsRasterLayer


class TestEnviUtils(TestCase):

    def test(self):
        # Case with non-matching classes
        layers = [QgsRasterLayer(landcover_map_l2, 'landcover_map_l2'),
                  QgsRasterLayer(landcover_map_l3, 'landcover_map_l3')]
        # Case with many classes
        layers = [QgsRasterLayer(r'D:\data\CORINE\U2000_CLC1990_V2020_20u1.tif', '1990'),
                  QgsRasterLayer(r'D:\data\CORINE\U2006_CLC2000_V2020_20u1.tif', '2006'),
                  QgsRasterLayer(r'D:\data\CORINE\U2018_CLC2018_V2020_20u1.tif', '2018')]
        # Case with many maps
        layers = [QgsRasterLayer(rf'D:\data\timeseries\MAP_BLCM_{i}.tif', str(i)) for i in range(2014, 2021)]

        builder = LandCoverChangeSankeyPlotBuilder(layers)
        fig = builder.sankeyPlot(layers[0].extent(), 250000, 0, True, True, True, False, False)
        fig.show()
