collection = ee.ImageCollection("COPERNICUS/S3/OLCI")

# default colors for bands and spectral indices
bandColors = {
    'Oa04_radiance': '#003fbd', 'Oa06_radiance': '#008700', 'Oa08_radiance': '#c50003', 'Oa17_radiance': '#af54ff',
    # vegetation
    'NDVI': '#aaff00', 'EVI': '#007d00', 'ARVI': '#007d00', 'SAVI': '#007d00', 'SARVI': '#007d00',
    # water
    'NDWI': '#0000ff',
}

# mapping from spectral index formular identifiers to image bands
wavebandMapping = {
    'A': 'Oa03_radiance', 'B': 'Oa04_radiance', 'G': 'Oa06_radiance', 'R': 'Oa08_radiance', 'N': 'Oa17_radiance'
}
