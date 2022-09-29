from osgeo import gdal

from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.rasterwriter import RasterWriter
from qgis.core import QgsVectorLayer

app = start_app()

vector = QgsVectorLayer(r'D:\data\country_health_2018\country_health_ranking_2018.geojson')

fieldNames = [field.name() for field in vector.fields()
              if field.name().startswith('Percent')]
print(fieldNames)

filenames = list()
for name in fieldNames:
    alg = RasterizeVectorAlgorithm()
    parameters = {
        alg.P_VECTOR: vector,
        alg.P_BURN_ATTRIBUTE: name,
        alg.P_INIT_VALUE: -9999,
        alg.P_GRID: r'D:\data\country_health_2018\grid.tif',
        alg.P_OUTPUT_RASTER: rf'D:\data\\country_health_2018\tmp\{name}.tif'
    }
    filenames.append(parameters[alg.P_OUTPUT_RASTER])
    alg.runAlg(alg, parameters, None, None, None, False)
    ds = gdal.Open(filenames[-1])
    ds.GetRasterBand(1).SetNoDataValue(-9999)
    ds.GetRasterBand(1).SetDescription(name)

ds = gdal.BuildVRT(r'D:\data\country_health_2018\country_health_2018.vrt', filenames, separate=True)
writer = RasterWriter(ds)
for bandNo, name in enumerate(fieldNames, 1):
    writer.setBandName(name, bandNo)
writer.close()
del ds, writer

exit()
