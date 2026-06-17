from qgis._core import QgsCoordinateReferenceSystem

from enmapbox.qgispluginsupport.qps.utils import SpatialPoint



def conversion(old):
    # adopted from https://stackoverflow.com/questions/10852955/
    # python-batch-convert-gps-positions-to-lat-lon-decimals
    #53°04'29.2"N 13°53'42.3"E
    direction = {'N': 1, 'S': -1, 'E': 1, 'W': -1}
    new = old.replace(u'°', ' ').replace('\'', ' ').replace('"', ' ')
    new = new.split()
    new_dir = new.pop()
    new.extend([0, 0, 0])
    return (int(new[0]) + int(new[1]) / 60.0 + float(new[2]) / 3600.0) * direction[new_dir]

x=SpatialPoint(QgsCoordinateReferenceSystem.fromEpsgId(4326), conversion("""53°0d4'29.2"N"""), conversion("""53°04'29.2"N"""))
print(x)

exit()
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app

qgsApp = start_app()

darkMode = False
if darkMode:
    qgsApp.setStyle('Fusion')
    qgsApp.setUITheme('Night Mapping')

initAll()
enmapBox = EnMAPBox()

# enmapBox.ui.setFixedSize(1920 - 2, 1080 - 32)  # for recording 1080p videos with ScreenToGif

enmapBox.openExampleData(mapWindows=2)
qgsApp.exec_()
