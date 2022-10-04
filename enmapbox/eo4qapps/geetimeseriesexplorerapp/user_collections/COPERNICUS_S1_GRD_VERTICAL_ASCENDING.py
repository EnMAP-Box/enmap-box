# Code provided by Juan Doblas.
# Title: Sentinel-1 Ascending orbits - unfiltered
# ID: COPERNICUS_S1_GRD
#
# This collection returns unfiltered Sentinel-1 Images in ascending orbits.
# Units are db, g0 stands for angle-corrected intensity, dev for deviation from collection median.
# Angle-correction is taken from the algorithm developped by Guido Lemoine and  Felix Greifeneder.
# Use larger sampling scales (>100 m) to avoid speckle.
# Thoughts, doubts, suggestions: juandb@gmail.com.


import ee
import math


def toDB(img):
    return ee.Image(ee.Image(img).log10().multiply(10.0).copyProperties(img, ['system:time_start', 'sliceNumber']))


def toGamma0natural(img):
    # WARNING: INPUT VALUES MUST BE IN linear scale!!!! BAND0: VV BAND1:VH
    img = img.addBands(getLIA(img).rename('LIA'))  # Computes Local Incidence Angle (LIA) band
    lia = img.select('LIA')
    vv_gamma0 = img.select(0).divide(lia.multiply(math.pi / 180.0).cos())
    vh_gamma0 = img.select(1).divide(lia.multiply(math.pi / 180.0).cos())
    return img.addBands(vv_gamma0.rename('VVg0')).addBands(vh_gamma0.rename('VHg0')).addBands(lia.rename('LIA'))


# / Compute local incidence angle    #/
# / by Felix Greifeneder, Guido Lemoine #/
def getLIA(img):
    srtm = ee.Image('USGS/SRTMGL1_003')  # Loads MDT
    s1_inc = img.select('angle')
    s1_azimuth = ee.Terrain.aspect(s1_inc) \
        .reduceRegion(ee.Reducer.mean(), s1_inc.get('system:footprint'), 100) \
        .get('aspect')
    azimuthEdge = getDESCCorners(img)
    TrueAzimuth = azimuthEdge.get(
        'azimuth')  # This should be some degree off the South direction (180), due to Earth rotation
    rotationFromSouth = ee.Number(TrueAzimuth).subtract(180.0)
    s1_azimuth = ee.Number(s1_azimuth).add(rotationFromSouth)
    srtm_slope = ee.Terrain.slope(srtm).select('slope')
    srtm_aspect = ee.Terrain.aspect(srtm).select('aspect')
    slope_projected = srtm_slope.multiply(
        ee.Image.constant(TrueAzimuth).subtract(90.0).subtract(srtm_aspect).multiply(math.pi / 180).cos())
    lia = s1_inc.subtract(ee.Image.constant(90).subtract(ee.Image.constant(90).subtract(slope_projected))).abs()
    return lia


# Calculate True azimuth direction for  the near range image edge
def getDESCCorners(f):
    # Get the coords as a transposed array
    coords = ee.Array(f.geometry().coordinates().get(0)).transpose()
    crdLons = ee.List(coords.toList().get(0))
    crdLats = ee.List(coords.toList().get(1))
    minLon = crdLons.sort().get(0)
    maxLon = crdLons.sort().get(-1)
    minLat = crdLats.sort().get(0)
    maxLat = crdLats.sort().get(-1)
    azimuth = ee.Number(crdLons.get(crdLats.indexOf(minLat))).subtract(minLon) \
        .atan2(ee.Number(crdLats.get(crdLons.indexOf(minLon))).subtract(minLat)) \
        .multiply(180.0 / math.pi) \
        .add(180.0)
    return ee.Feature(ee.Geometry.LineString([crdLons.get(crdLats.indexOf(maxLat)), maxLat,
                                              minLon, crdLats.get(crdLons.indexOf(minLon))]),
                      {'azimuth': azimuth}).copyProperties(f)


bands = ee.List(['VH', 'VV', 'VHg0', 'VVg0', 'Ratio', 'VH_dev', 'VV_dev', 'VHg0_dev', 'VVg0_dev', 'Ratio_dev'])
band_names = ee.List(
    ['VH', 'VV', 'VHg0', 'VVg0', 'Ratio VVg0/VHg0', 'VV_dev', 'VH_dev', 'VHg0_dev', 'VVg0_dev', 'Ratio_dev'])

S1col = ee.ImageCollection("COPERNICUS/S1_GRD_FLOAT") \
    .filterMetadata('instrumentMode', 'equals', 'IW') \
    .filterMetadata('orbitProperties_pass', 'equals', 'ASCENDING') \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .select('VV', 'VH', 'angle') \
    .map(toGamma0natural) \
    .select('VH', 'VV', 'VHg0', 'VVg0') \
    .map(toDB) \
    .map(lambda image: image.addBands(image.select('VVg0').subtract(image.select('VHg0')).rename('Ratio')))

S1col = S1col.map(lambda image: image.addBands(image.subtract(S1col.median())).rename(
    ['VH', 'VV', 'VHg0', 'VVg0', 'Ratio', 'VH_dev', 'VV_dev', 'VHg0_dev', 'VVg0_dev', 'Ratio_dev']))

bandColors = {
    'VH': '#fdae61',
    'VV': '#a6d96a',
    'VHg0': '#d7191c',
    'VVg0': '#1a9641',
    'ratio': '#ffffbf',
    'VH_dev': '#dfc27d',
    'VV_dev': '#80cdc1',
    'VHg0_dev': '#a6611a',
    'VVg0_dev': '#018571',
    'ratio_dev': '#f5f5f5',
}

collection = S1col
