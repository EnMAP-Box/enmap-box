collection = ee.ImageCollection("COPERNICUS/S1_GRD")

# remove HH and HV bands
collection = collection \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))

# default colors for bands and spectral indices
bandColors = {}
