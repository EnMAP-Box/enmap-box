import processing
from enmapbox import initAll
from enmapbox.testing import start_app

start_app()
initAll()

# prepare dataset
algName = 'enmapbox:TranslateRasterLayer'
parameters = {
    'raster': r'D:\source\QGISPlugIns\enmap-box\enmapbox\exampledata\enmap_potsdam.tif',
    'outputTranslatedRaster': 'c:/test/copy.tif'
}
processing.run(algName, parameters)
