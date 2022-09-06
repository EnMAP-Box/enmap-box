import numpy as np

from enmapbox import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.driver import Driver
from qgis.core import QgsRasterLayer

qgsApp = start_app()
enmapBox = EnMAPBox(load_other_apps=False)

# create a layer that reports his wavelength via Provider.wavelength
Driver('test.tif').createFromArray(np.array(list(range(3 * 2 * 2))).reshape((3, 2, 2)))
layer = QgsRasterLayer('test.tif', 'test')
provider = layer.dataProvider()
provider.wavelength = lambda bandNo: 42 + bandNo
provider.name = lambda: 'dummy'  # GDAL provider is not allowed to report his wavelength, so we overwrite the name

enmapBox.onDataDropped([layer])
qgsApp.exec_()
