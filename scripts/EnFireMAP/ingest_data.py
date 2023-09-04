from collections import defaultdict
from os import listdir, makedirs, sep
from os.path import join, isdir, dirname, exists, normpath
from typing import Optional

from osgeo.gdal import BuildVRT, Warp, WarpOptions, Translate, TranslateOptions

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from qgis._core import QgsVectorLayer

rootData = r'D:\data\EnFireMap\data'
rootCube = r'D:\data\EnFireMap\cube'
rootTmpWarped = r'D:\data\EnFireMap\data\_warped'
rootTmpMosaics = r'D:\data\EnFireMap\data\_mosaics'
tilingScheme = QgsVectorLayer(r'D:\data\EnFireMap\cube\shp\grid.shp')
idField = 'Tile_ID'

products = [
    'QL_PIXELMASK.TIF', 'QL_QUALITY_CIRRUS.TIF', 'QL_QUALITY_CLASSES.TIF', 'QL_QUALITY_CLOUD.TIF',
    'QL_QUALITY_CLOUDSHADOW.TIF', 'QL_QUALITY_HAZE.TIF', 'QL_QUALITY_SNOW.TIF', 'QL_QUALITY_TESTFLAGS.TIF',
    'QL_SWIR.TIF', 'QL_VNIR.TIF', 'SPECTRAL_IMAGE.vrt'
]


def prepareSpectralImages():
    for name in listdir(rootData):
        if isdir(join(rootData, name)):
            xmlFilename = auxFindMetadataXml(join(rootData, name))
            if xmlFilename is not None:
                alg = ImportEnmapL2AAlgorithm()
                parameters = {
                    alg.P_FILE: xmlFilename,
                    alg.P_SET_BAD_BANDS: True,
                    alg.P_EXCLUDE_BAD_BANDS: True,
                    alg.P_DETECTOR_OVERLAP: alg.OrderByWavelengthOverlapOption,
                    alg.P_OUTPUT_RASTER: xmlFilename.replace('METADATA.XML', 'SPECTRAL_IMAGE.vrt'),
                }
                alg.runAlg(alg, parameters)


def ingestData():
    # group by date
    scenesByDate = defaultdict(list)
    for scene in listdir(rootData):
        try:
            prefix, datestamp, sceneNo = scene.split('_')
            assert prefix == 'nc'
        except:
            continue
        scenesByDate[datestamp].append(scene)

    # build mosaic for each date and product
    filesByDateAndProduct = defaultdict(list)
    for datestamp, scenes in scenesByDate.items():
        for scene in scenes:
            print('warp', scene, flush=True)
            xmlFilename = auxFindMetadataXml(join(rootData, scene))
            for product in products:
                productFilename = xmlFilename.replace('METADATA.XML', product)
                tmp = normpath(productFilename).split(sep)
                productFilename2 = join(rootTmpWarped, *tmp[-2:])
                if not exists(dirname(productFilename2)):
                    makedirs(dirname(productFilename2))
                options = WarpOptions(
                    format='GTiff', dstSRS=tilingScheme.crs().toWkt(),
                    creationOptions=Driver.DefaultGTiffCreationOptions
                )
                Warp(productFilename2, productFilename, options=options)

                filesByDateAndProduct[(datestamp, product)].append(productFilename2)

    # - mosaic and cut into tiling scheme
    for (datestamp, product), filenames in filesByDateAndProduct.items():
        print('mosaic', datestamp + '_' + product, flush=True)
        if not exists(join(rootTmpMosaics, datestamp)):
            makedirs(join(rootTmpMosaics, datestamp))
        filename = join(rootTmpMosaics, datestamp, datestamp + '_' + product).replace('.TIF', '.vrt')
        BuildVRT(filename, filenames)

        reader = RasterReader(filename)
        extent = SpatialExtent(reader.crs(), reader.extent())
        extent2 = extent.toCrs(tilingScheme.crs())
        tilingScheme.selectByRect(extent2)
        for feature in tilingScheme.selectedFeatures():
            tileName = str(feature.attribute(idField))
            print('cut', tileName, datestamp + '_' + product, flush=True)
            filename2 = join(rootCube, tileName, datestamp + '_' + product).replace('.vrt', '.TIF')
            if not exists(join(rootCube, tileName)):
                makedirs(join(rootCube, tileName))
            tileExtent = feature.geometry().boundingBox()
            projWin = tileExtent.xMinimum(), tileExtent.yMaximum(), tileExtent.xMaximum(), tileExtent.yMinimum()
            options = TranslateOptions(
                format='GTiff', projWin=projWin, creationOptions=Driver.DefaultGTiffCreationOptions
            )
            Translate(filename2, filename, options=options)


def auxFindMetadataXml(folder: str) -> Optional[str]:
    for name in listdir(folder):
        if name.endswith('METADATA.XML'):
            return join(folder, name)
    return None


# prepareSpectralImages()
ingestData()
print('done')
