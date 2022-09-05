import datetime
import os
import pathlib
import re
import shutil
import time
from typing import List, Match

from osgeo import gdal

from enmapbox.qgispluginsupport.qps.utils import file_search
from enmapbox.testing import start_app
from qgis.PyQt.QtCore import QDateTime
from qgis.core import QgsCoordinateTransform, QgsFeatureRequest, Qgis
from qgis.core import QgsVectorLayer, QgsFeature, QgsPointXY, QgsGeometry, QgsVectorFileWriter, \
    QgsCoordinateTransformContext

app = start_app()

DIR_IMAGES = r'S:\SenseCarbon\Data\FieldTrip2014\08_Pictures'
# DIR_IMAGES = r'S:\SenseCarbon\Data\FieldTrip2014\08_Pictures\BJ_GPS'
DIR_IMAGES = pathlib.Path(DIR_IMAGES)
OVERWRITE = True
KEEP_CHILDPATH = True
DIR_OUTPUT = pathlib.Path(r'S:\SenseCarbon\Data\FieldTrip2014\08_PictureCoordinates')
DIR_OUTPUT = pathlib.Path(r'T:\LN\Amazon-MAP')
AOI_PATH = r'J:\diss_bj\level2\s-america\shp\grid.shp'
AOI_FILTER_EXPRESSION = "Tile_ID = 'X0049_Y0026'"

DIR_OUTPUT_IMG = DIR_OUTPUT / 'pictures'
PATH_VECTOR = DIR_OUTPUT / 'PICTURE_POSITIONS.gpkg'

assert DIR_IMAGES.is_dir()

os.makedirs(DIR_OUTPUT_IMG, exist_ok=True)

rx_images = re.compile(r'\.jpg$', re.I)
rx_deg_min_sec = re.compile(r'\((?P<deg>\d+)\) \((?P<min>\d+)\) \((?P<sec>\d+\.\d+)\)')
rx_float = re.compile(r'\((?P<angle>[-+.\d]+)\)')

uri = "point?crs=epsg:4326&" \
      "field=name:string&" \
      "field=lat:double&" \
      "field=lon:double&" \
      "field=datetime:datetime&" \
      "field=direction:double&" \
      "field=orientation:int&" \
      "field=rotation:int&" \
      "field=mirror:string(1)&" \
      "field=path_rel:string&" \
      "index=yes"

lyr = QgsVectorLayer(uri, 'GPS Locations', 'memory')
lyr.startEditing()

tStart = datetime.datetime.now()
t0 = datetime.datetime.now()
tdelta = datetime.timedelta(seconds=3)

features: List[QgsFeature] = []

lyrAOI: QgsVectorLayer = False
AOI_GEOMETRIES: List[QgsFeature] = []
if AOI_PATH:
    lyrAOI = QgsVectorLayer(pathlib.Path(AOI_PATH).as_posix())

    crsTrans = QgsCoordinateTransform()
    crsTrans.setSourceCrs(lyrAOI.crs())
    crsTrans.setDestinationCrs(lyr.crs())

    aoiFeatureRequest = QgsFeatureRequest()
    if AOI_FILTER_EXPRESSION:
        aoiFeatureRequest.setFilterExpression(AOI_FILTER_EXPRESSION)

    for f in lyrAOI.getFeatures(aoiFeatureRequest):
        f: QgsFeature
        g = f.geometry()
        assert g.transform(crsTrans) == Qgis.GeometryOperationResult.Success
        AOI_GEOMETRIES.append(g)

image_ids = set()
print(f'Search for image candidates below {DIR_IMAGES}...')
candidate_images = list(file_search(DIR_IMAGES, rx_images, recursive=True))
print(f'Found {len(candidate_images)} image candidates')

# see https://exiftool.org/TagNames/EXIF.html
EXIF_ORIENTATION2ROTATION = {
    1: 0,  # Horizontal (normal)
    2: 0,  # Mirror horizontal
    3: 180,  # Rotate 180
    4: 0,  # Mirror vertical
    5: 270,  # Mirror horizontal and rotate 270 CW
    6: 90,  # Rotate 90 CW
    7: 0,  # Mirror horizontal and rotate 90 CW
    8: 270  # Rotate 270 CW
}

EXIF_ORIENTATION2MIRROR = {
    1: None,  # Horizontal (normal)
    2: 'h',  # Mirror horizontal
    3: None,  # Rotate 180
    4: 'v',  # Mirror vertical
    5: 'h',  # Mirror horizontal and rotate 270 CW
    6: None,  # Rotate 90 CW
    7: 'h',  # Mirror horizontal and rotate 90 CW
    8: None  # Rotate 270 CW
}

for i, file in enumerate(candidate_images):

    ds: gdal.Dataset = gdal.Open(file)
    # see https://exiftool.org/TagNames/GPS.html
    if not isinstance(ds, gdal.Dataset):
        s = ""
        continue

    exif_datetime = None
    for k in ['EXIF_DateTimeOriginal', 'EXIF_DateTimeDigitized', 'EXIF_DateTime']:
        exif_datetime = ds.GetMetadataItem(k)
        if isinstance(datetime, str):
            break

    exif_lat = ds.GetMetadataItem('EXIF_GPSLatitude')
    exif_lon = ds.GetMetadataItem('EXIF_GPSLongitude')

    if not (isinstance(exif_lon, str) and isinstance(exif_lat, str)):
        s = ""
        continue

    exif_lat = rx_deg_min_sec.match(exif_lat)
    exif_lon = rx_deg_min_sec.match(exif_lon)

    if not (isinstance(exif_lat, Match) and isinstance(exif_lon, Match)):
        raise Exception('Unable to extract degrees, seconds and minutes')

    exif_lat = \
        float(exif_lat.group('deg')) + \
        float(exif_lat.group('min')) / 60 + \
        float(exif_lat.group('sec')) / 3600

    exif_lon = \
        float(exif_lon.group('deg')) + \
        float(exif_lon.group('min')) / 60 + \
        float(exif_lon.group('sec')) / 3600

    image_id = (exif_datetime, exif_lon, exif_lat)

    if image_id in image_ids:
        print(f'Image already added: {file}')
        continue

    if ds.GetMetadataItem('EXIF_GPSLatitudeRef') in ['S']:
        exif_lat *= -1

    if ds.GetMetadataItem('EXIF_GPSLongitudeRef') in ['W']:
        exif_lon *= -1

    pt = QgsPointXY(exif_lon, exif_lat)
    g = QgsGeometry.fromPointXY(pt)

    if len(AOI_GEOMETRIES) > 0:
        keep = False
        for gAOI in AOI_GEOMETRIES:
            gAOI: QgsGeometry
            if gAOI.contains(g) or gAOI.touches(g):
                keep = True
                break
        if not keep:
            continue

    exif_direction = ds.GetMetadataItem('EXIF_GPSImgDirection')
    exif_orientation = ds.GetMetadataItem('EXIF_Orientation')
    if isinstance(exif_direction, str):
        exif_direction = float(rx_float.match(exif_direction).group('angle'))

    if isinstance(exif_orientation, str):
        exif_orientation = int(exif_orientation)

    feature = QgsFeature(lyr.fields())
    feature.setGeometry(g)

    filepath = pathlib.Path(file)
    if KEEP_CHILDPATH:
        new_file = DIR_OUTPUT_IMG / filepath.relative_to(DIR_IMAGES)
    else:
        new_file = DIR_OUTPUT_IMG / filepath.name
    os.makedirs(new_file.parent, exist_ok=True)
    if new_file.is_file():

        file_c_time = time.ctime(os.path.getctime(new_file))
        file_c_time = datetime.datetime.strptime(file_c_time, "%a %b %d %H:%M:%S %Y")

        # do not overwrite pictures with same name
        if not OVERWRITE or file_c_time > tStart:

            iFile = 1
            bn, ext = os.path.splitext(os.path.basename(filepath.name))
            while new_file.is_file():
                new_file = DIR_OUTPUT_IMG / f'{bn}.{iFile}{ext}'
                iFile += 1
    shutil.copyfile(filepath, new_file)

    feature.setAttribute('name', new_file.name)
    # feature.setAttribute('path_abs', new_file.as_posix())
    feature.setAttribute('path_rel', new_file.relative_to(PATH_VECTOR.parent).as_posix())
    feature.setAttribute('lat', exif_lat)
    feature.setAttribute('lon', exif_lon)
    feature.setAttribute('datetime', QDateTime.fromString(exif_datetime, 'yyyy:MM:dd hh:mm:ss'))
    feature.setAttribute('direction', exif_direction)
    feature.setAttribute('orientation', exif_orientation)
    if exif_orientation:
        feature.setAttribute('rotation', EXIF_ORIENTATION2ROTATION.get(exif_orientation, 0))
        feature.setAttribute('mirror', EXIF_ORIENTATION2MIRROR.get(exif_orientation, None))
    features.append(feature)

    if datetime.datetime.now() - t0 > tdelta:
        print(f'Checked {i + 1} files, found {len(features)} with coordinates')
        t0 = datetime.datetime.now()

print(f'Add {len(features)} features to memory layer')
lyr.startEditing()
assert lyr.addFeatures(features)
assert lyr.commitChanges()

print(f'Write memory layer to {PATH_VECTOR}')
ogrDataSourceOptions = []
ogrLayerOptions = [
    'IDENTIFIER=Pictures',
    'DESCRIPTION=Picture coordinates']

options = QgsVectorFileWriter.SaveVectorOptions()
options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
# options.feedback = feedback
options.datasourceOptions = ogrDataSourceOptions
options.layerOptions = ogrLayerOptions
options.fileEncoding = 'UTF-8'
options.skipAttributeCreation = False
options.driverName = 'GPKG'

transformationContext = QgsCoordinateTransformContext()

writer: QgsVectorFileWriter = QgsVectorFileWriter.create(PATH_VECTOR.as_posix(),
                                                         lyr.fields(),
                                                         lyr.wkbType(),
                                                         lyr.crs(),
                                                         transformationContext,
                                                         options)
if writer.hasError() != QgsVectorFileWriter.NoError:
    raise Exception(f'Error when creating {PATH_VECTOR.as_posix()}: {writer.errorMessage()}')

if not writer.addFeatures(lyr.getFeatures()):
    if writer.errorCode() != QgsVectorFileWriter.NoError:
        raise Exception(f'Error when creating feature: {writer.errorMessage()}')

# important! to call flush
del writer
