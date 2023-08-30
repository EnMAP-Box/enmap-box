from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import decodeProfileValueDict
from qgis.core import QgsVectorLayer

layer = QgsVectorLayer(r'D:\source\QGISPlugIns\enmap-box\enmapbox\exampledata\library_berlin.gpkg')
layer.selectAll()
for feature in layer.selectedFeatures():
    dump = feature.attribute('profiles')
    print(decodeProfileValueDict(dump))
    break
