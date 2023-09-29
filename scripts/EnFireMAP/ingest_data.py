import shutil
from collections import defaultdict
from os import listdir, makedirs, sep
from os.path import join, isdir, dirname, exists, normpath, basename
from typing import Optional
from xml.etree import ElementTree

from osgeo import gdal

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from qgis.core import QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, \
    QgsProject, QgsVectorLayer, QgsGeometry

rootData = r'D:\data\EnFireMap\data'
rootCube = r'D:\data\EnFireMap\cube'
rootTmpWarped = r'D:\data\EnFireMap\data\_warped'
rootTmpMosaics = r'D:\data\EnFireMap\data\_mosaics'
tilingScheme = QgsVectorLayer(r'D:\data\EnFireMap\cube\shp\grid2.geojson')
assert tilingScheme.isValid()
idField = 'Tile_ID'

products = [
    'QL_PIXELMASK.TIF', 'QL_QUALITY_CIRRUS.TIF', 'QL_QUALITY_CLASSES.TIF', 'QL_QUALITY_CLOUD.TIF',
    'QL_QUALITY_CLOUDSHADOW.TIF', 'QL_QUALITY_HAZE.TIF', 'QL_QUALITY_SNOW.TIF', 'QL_QUALITY_TESTFLAGS.TIF',
    'QL_SWIR.TIF', 'QL_VNIR.TIF', 'SPECTRAL_IMAGE.vrt'
]
productNoDataValues = defaultdict(lambda: 0)
productNoDataValues['QL_PIXELMASK.TIF'] = 255


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


def copyMetadataXml():
    for name in listdir(rootData):
        if isdir(join(rootData, name)):
            xmlFilename = auxFindMetadataXml(join(rootData, name))
            if xmlFilename is not None:
                boundingPolygon = auxDeriveSceneBoundingPolygon(xmlFilename)
                sourceCrs = QgsCoordinateReferenceSystem(4326)
                destCrs = tilingScheme.crs()
                tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                boundingPolygon.transform(tr)
                tilingScheme.selectByRect(boundingPolygon.boundingBox())
                for feature in tilingScheme.selectedFeatures():  # course selection via bounding box
                    if not feature.geometry().intersects(boundingPolygon):  # fine selection
                        continue
                    tileName = str(feature.attribute(idField))
                    print('copy', tileName, basename(xmlFilename), flush=True)
                    filename2 = join(rootCube, tileName, basename(xmlFilename))
                    if not exists(join(rootCube, tileName)):
                        makedirs(join(rootCube, tileName))
                    if not exists(filename2):
                        shutil.copyfile(xmlFilename, filename2)


def ingestData():
    # group by date
    scenesByDate = defaultdict(list)
    for scene in listdir(rootData):
        try:
            prefix, datestamp, sceneNo = scene.split('_')
            assert prefix == 'nc'
        except Exception:
            continue
        scenesByDate[datestamp].append(scene)

    # build mosaic for each date and product
    filesByDateAndProduct = defaultdict(list)
    boundingPolygonsByDate = defaultdict(list)
    for datestamp, scenes in scenesByDate.items():
        for scene in scenes:
            print('warp', scene, flush=True)
            xmlFilename = auxFindMetadataXml(join(rootData, scene))
            boundingPolygon = auxDeriveSceneBoundingPolygon(xmlFilename)
            boundingPolygonsByDate[datestamp].append(boundingPolygon)

            for product in products:
                productFilename = xmlFilename.replace('METADATA.XML', product)
                tmp = normpath(productFilename).split(sep)
                productFilename2 = join(rootTmpWarped, *tmp[-2:])
                if not exists(dirname(productFilename2)):
                    makedirs(dirname(productFilename2))
                # derive correct target grid to avoid later resampling
                reader = RasterReader(productFilename)
                extent = SpatialExtent(reader.crs(), reader.extent())
                extent2 = extent.toCrs(tilingScheme.crs())
                tilingScheme.selectByRect(extent2)
                geometries = [feature.geometry() for feature in tilingScheme.selectedFeatures()]
                bb = QgsGeometry.unaryUnion(geometries).boundingBox()
                outputBounds = (bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum())
                # warp
                srcNoData = reader.noDataValue(1)
                if srcNoData is None:
                    srcNoData = productNoDataValues[product]
                options = gdal.WarpOptions(
                    format='GTiff', dstSRS=tilingScheme.crs().toWkt(), outputBounds=outputBounds,
                    creationOptions=Driver.DefaultGTiffCreationOptions,
                    xRes=reader.rasterUnitsPerPixelX(), yRes=reader.rasterUnitsPerPixelY(),
                    srcNodata=srcNoData
                )
                if not exists(productFilename2):
                    gdal.Warp(productFilename2, productFilename, options=options)
                filesByDateAndProduct[(datestamp, product)].append(productFilename2)

    # - mosaic and cut into tiling scheme
    for (datestamp, product), filenames in filesByDateAndProduct.items():
        print('mosaic', datestamp + '_' + product, flush=True)
        if not exists(join(rootTmpMosaics, datestamp)):
            makedirs(join(rootTmpMosaics, datestamp))
        filename = join(rootTmpMosaics, datestamp, datestamp + '_' + product).replace('.TIF', '.vrt')
        if not exists(filename):
            gdal.BuildVRT(filename, filenames)
        reader = RasterReader(filename)
        # extent = SpatialExtent(reader.crs(), reader.extent())
        # extent2 = extent.toCrs(tilingScheme.crs())
        boundingPolygon = QgsGeometry.unaryUnion(boundingPolygonsByDate[datestamp])
        sourceCrs = QgsCoordinateReferenceSystem(4326)
        destCrs = reader.crs()
        tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
        boundingPolygon.transform(tr)

        # get bounding polygon from all individual scenes and build union -> removes the empty tiles!
        tilingScheme.selectByRect(boundingPolygon.boundingBox())
        for feature in tilingScheme.selectedFeatures():  # course selection via bounding box
            if not feature.geometry().intersects(boundingPolygon):  # fine selection
                continue
            tileName = str(feature.attribute(idField))
            print('cut', tileName, 'ENMAPL2A_' + datestamp + '_' + product, flush=True)
            filename2 = join(rootCube, tileName, 'ENMAPL2A_' + datestamp + '_' + product).replace('.vrt', '.TIF')
            if not exists(join(rootCube, tileName)):
                makedirs(join(rootCube, tileName))
            tileExtent = feature.geometry().boundingBox()
            projWin = tileExtent.xMinimum(), tileExtent.yMaximum(), tileExtent.xMaximum(), tileExtent.yMinimum()
            options = gdal.TranslateOptions(
                format='GTiff', projWin=projWin, creationOptions=Driver.DefaultGTiffCreationOptions
            )
            if not exists(filename2):
                ds = gdal.Translate(filename2, filename, options=options)

                if product == 'SPECTRAL_IMAGE.vrt':
                    # copy metadata
                    reader = RasterReader(filesByDateAndProduct[(datestamp, 'SPECTRAL_IMAGE.vrt')][0])
                    writer = RasterWriter(ds)
                    writer.setMetadata(reader.metadata())
                    for bandNo in reader.bandNumbers():
                        writer.setMetadata(reader.metadata(bandNo), bandNo)
                        writer.setBandName(reader.bandName(bandNo), bandNo)


def auxFindMetadataXml(folder: str) -> Optional[str]:
    for name in listdir(folder):
        if name.endswith('METADATA.XML'):
            return join(folder, name)
    return None


def auxDeriveSceneBoundingPolygon(xmlFilename) -> QgsGeometry:
    # get bounding polygon
    root = ElementTree.parse(xmlFilename).getroot()
    points = dict()
    for point in root.findall('base/spatialCoverage/boundingPolygon/point'):
        key = point.find('frame').text
        x = point.find('longitude').text
        y = point.find('latitude').text
        points[key] = QgsPointXY(float(x), float(y))
    boundingPolygon = QgsGeometry.fromPolygonXY(
        [[points[key] for key in ['upper_left', 'upper_right', 'lower_right', 'lower_left']]]
    )
    return boundingPolygon


prepareSpectralImages()
copyMetadataXml()
ingestData()
print('done')
