from os import listdir, makedirs
from os.path import dirname, exists, join

from qgis.core import QgsVectorFileWriter, QgsVectorLayer

from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.samplerastervaluesalgorithm import SampleRasterValuesAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm

rootCube = r'D:\data\EnFireMap\cube'
tilingScheme = QgsVectorLayer(r'D:\data\EnFireMap\cube\shp\grid2.geojson')
idField = 'Tile_ID'

products = [
    'QL_PIXELMASK.TIF', 'QL_QUALITY_CIRRUS.TIF', 'QL_QUALITY_CLASSES.TIF', 'QL_QUALITY_CLOUD.TIF',
    'QL_QUALITY_CLOUDSHADOW.TIF', 'QL_QUALITY_HAZE.TIF', 'QL_QUALITY_SNOW.TIF', 'QL_QUALITY_TESTFLAGS.TIF',
    'QL_SWIR.TIF', 'QL_VNIR.TIF', 'SPECTRAL_IMAGE.vrt'
]
products = [
    'SPECTRAL_IMAGE.TIF'
]

locations = QgsVectorLayer(r'D:\data\EnFireMap\lib_points\lib_points.shp')
rootOutputSample = r'D:\data\EnFireMap\sample3'

qgsApp = start_app()
initAll()


def sampleData():
    tilingScheme.selectByRect(locations.extent())
    for feature in tilingScheme.selectedFeatures():
        tileName = str(feature.attribute(idField))
        if not exists(join(rootCube, tileName)):
            continue
        for name in listdir(join(rootCube, tileName)):
            for product in products:
                if name.endswith(product):
                    print('sample', tileName, name, flush=True)
                    filename = join(rootCube, tileName, name)
                    filename2 = join(rootOutputSample, tileName, name + '.geojson')
                    filenamePoints = join(rootOutputSample, tileName, name + '.points.gpkg')
                    if not exists(dirname(filenamePoints)):
                        makedirs(dirname(filenamePoints))

                    locations.selectByRect(feature.geometry().boundingBox())
                    QgsVectorFileWriter.writeAsVectorFormat(
                        locations, filenamePoints, "UTF-8", locations.crs(), onlySelected=True)

                    alg = SampleRasterValuesAlgorithm()
                    parameters = {
                        alg.P_RASTER: filename,
                        alg.P_VECTOR: filenamePoints,
                        alg.P_SKIP_NO_DATA_PIXEL: True,
                        alg.P_OUTPUT_POINTS: filename2
                    }
                    EnMAPProcessingAlgorithm.runAlg(alg, parameters)


sampleData()
print('done')
