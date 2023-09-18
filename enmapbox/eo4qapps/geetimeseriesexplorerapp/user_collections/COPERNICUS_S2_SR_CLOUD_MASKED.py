# Title: Sentinel-2 MSI: MultiSpectral Instrument, Level-2A with aggressive cloud masking
# ID: COPERNICUS_S2_SR_HARMONIZED
#
# This collection returns the merged Sentinel-2A and -2B L2A (surface reflectance product) archives.
# It uses an aggressive cloud masking, fully discarding images with >50% cloud cover.
# Furthermore, the cloud displacement index (CDI; https://doi.org/10.1016/j.rse.2018.04.046 for details) is used to
# improve cloud masking.

collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

# filter cloudy images
collection = collection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))

# remove MSK_CLDPRB and MSK_SNWPRB bands, because they aren't available for all images
# remove QA_10 and QA_20 bands, because they are always empty
collection = collection.select([
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11', 'B12', 'AOT', 'WVP', 'SCL', 'TCI_R', 'TCI_G',
    'TCI_B', 'QA60'
])


# update mask using CDI
def maskS2cdi(image):
    cdi = ee.Algorithms.Sentinel2.CDI(image)
    return image.updateMask(cdi.gt(-0.8)).addBands(cdi)


collection = collection.map(maskS2cdi)

# default colors for bands and spectral indices
bandColors = {
    'B1': '55bbff', 'B2': '#003fbd', 'B3': '#008700', 'B4': '#c50003', 'B5': '#af54ff', 'B6': '#ffaf25',
    'B7': '#b87e1a', 'B8': '#af54ff', 'B8A': '#803ebe', 'B11': '#ffaf25', 'B12': '#b87e1a',
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
wavebandMapping = {
    'A': 'B1', 'B': 'B2', 'G': 'B3', 'R': 'B4', 'RE1': 'B5', 'RE2': 'B6', 'RE3': 'B7', 'RE4': 'B8A',
    'N': 'B8', 'S1': 'B11', 'S2': 'B12'
}

# set default QA flags
qaFlags = {
    "SCL": [
        "Saturated or defective", "Cloud Shadows", "Clouds Low Probability / Unclassified", "Clouds Medium Probability",
        "Clouds High Probability", "Cirrus", "Snow / Ice"]
}
