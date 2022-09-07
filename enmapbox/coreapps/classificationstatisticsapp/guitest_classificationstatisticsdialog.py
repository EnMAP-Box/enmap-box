from classificationstatisticsapp.classificationstatisticsdialog import ClassificationStatisticsDialog
from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from qgis.core import QgsRasterLayer, QgsVectorLayer

qgsApp = start_app()
initAll()

enmapBox = EnMAPBox(None)

layer = QgsRasterLayer(
    r'D:\data\CORINE\u2018_clc2018_v2020_20u1_raster100m\DATA\U2018_CLC2018_V2020_20u1.tif',
    'U2018_CLC2018_V2020_20u1.tif'
)
# layer = QgsRasterLayer(landcover_map_l3, 'landcover_map_l3.tif')
roiLayer = QgsVectorLayer(
    'D:/miniconda/envs/qgis/Library/resources/data/world_map.gpkg|layername=countries', 'world_map.gpkg'
)

mapDock = enmapBox.onDataDropped([layer, roiLayer])

widget = ClassificationStatisticsDialog(enmapBox.ui)
widget.show()
widget.mLayer.setLayer(layer)

qgsApp.exec_()
