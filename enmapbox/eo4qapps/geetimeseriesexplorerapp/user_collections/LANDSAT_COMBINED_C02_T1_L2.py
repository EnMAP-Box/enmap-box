import numpy as np

import ee

ee.Initialize()

# set unified band names
bandNames = ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'QA_PIXEL']

# combine all landsat collections
l4 = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') \
    .select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7', 'QA_PIXEL'], bandNames)
l5 = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
    .select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7', 'QA_PIXEL'], bandNames)
l7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
    .select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7', 'QA_PIXEL'], bandNames)
l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7', 'QA_PIXEL'], bandNames)
l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
    .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7', 'QA_PIXEL'], bandNames)

collections = [l4, l5, l7, l8, l9]

collection = ee.ImageCollection([])
for li in collections:
    collection = collection.merge(li)
# collection = ee.ImageCollection(ee.FeatureCollection(collections).flatten())

# restrict to common image properties available in all collections
propertyNames = ee.List([]) \
    .cat(l9.first().propertyNames()) \
    .cat(l8.first().propertyNames()) \
    .cat(l7.first().propertyNames()) \
    .cat(l5.first().propertyNames()) \
    .cat(l4.first().propertyNames()) \
    .sort().getInfo()
propertyNames = [
    name for name, count in zip(*np.unique(propertyNames, return_counts=True)) if count == len(collections)
]

# set default band colors
bandColors = {
    'BLUE': '#003fbd', 'GREEN': '#008700', 'RED': '#c50003', 'NIR': '#af54ff', 'SWIR1': '#ffaf25', 'SWIR2': '#b87e1a',
    'QA_PIXEL': '#b4b4b4',
    # vegetation
    'NDVI': '#aaff00', 'EVI': '#007d00', 'ARVI': '#007d00', 'SAVI': '#007d00', 'SARVI': '#007d00', 'NDMI': '#007d00',
    # burn
    'NBR': '#997700',
    # water
    'NDWI': '#0000ff', 'MNDWI': '#0000ff',
    # snow
    'NDSI': '#ffeedd',
    # soil
    'NDTI': '#eebb22',
    # urban
    'NDBI': '#ff0000',
    # other
    'TCB': '#ff0000', 'TCG': '#00ff00', 'TCW': '#0000ff', 'TCDI': '#ffff00'
}

# mapping from spectral index formular identifiers to image bands
wavebandMapping = {'B': 'BLUE', 'G': 'GREEN', 'R': 'RED', 'N': 'NIR', 'S1': 'SWIR1', 'S2': 'SWIR2'}

# set default QA flags
qaFlags = {
        "QA_PIXEL": ["Fill", "Dilated Cloud", "Cirrus (high confidence)", "Cloud", "Cloud Shadow", "Snow"]
}
