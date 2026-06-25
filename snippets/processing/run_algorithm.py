from pathlib import Path

import qgis.processing
from enmapbox import initAll
from enmapbox.exampledata import enmap as path_input
from enmapbox.testing import start_app

start_app()
initAll()

path_output = Path() / 'output.tif'

# prepare dataset
algName = 'enmapbox:translaterasterlayer'
parameters = {
    'raster': str(path_input),
    'outputTranslatedRaster': str(path_output)
}
qgis.processing.run(algName, parameters)
