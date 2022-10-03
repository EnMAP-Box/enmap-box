collection = ee.ImageCollection("MODIS/006/MOD09Q1")

# default colors for bands and spectral indices
bandColors = {
    'sur_refl_b01': '#c50003',
    'sur_refl_b02': '#af54ff',
    # vegetation
    'NDVI': '#aaff00'
}

# mapping from spectral index formular identifiers to image bands
wavebandMapping = {
    'R': 'sur_refl_b01',
    'N': 'sur_refl_b02'
}
