from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxtestdata import landcover_map_l2, landcover_map_l3
from landcoverchangestatisticsapp.landcoverchangestatisticsmainwindow import LandCoverChangeStatisticsMainWindow
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)
layers = [QgsRasterLayer(landcover_map_l2, 'landcover_map_l2'), QgsRasterLayer(landcover_map_l3, 'landcover_map_l3')]
layers = [QgsRasterLayer(r'D:\data\CORINE\U2000_CLC1990_V2020_20u1.tif', '1990'),
          QgsRasterLayer(r'D:\data\CORINE\U2006_CLC2000_V2020_20u1.tif', '2006'),
          QgsRasterLayer(r'D:\data\CORINE\U2018_CLC2018_V2020_20u1.tif', '2018')]
layers = [QgsRasterLayer(rf'D:\data\timeseries\MAP_BLCM_{i}.tif', str(i)) for i in range(2014, 2017)]
mapDock = enmapBox.onDataDropped(layers)

widget = LandCoverChangeStatisticsMainWindow()
widget.show()

widget.mSettingsDock.mLayers.setCurrentLayers(layers)
widget.onLayersChanged()

qgsApp.exec_()
