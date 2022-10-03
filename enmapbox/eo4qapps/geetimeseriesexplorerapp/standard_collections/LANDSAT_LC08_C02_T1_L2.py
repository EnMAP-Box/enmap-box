collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

# default colors for bands and spectral indices
bandColors = {
    'SR_B1': '55bbff', 'SR_B2': '#003fbd', 'SR_B3': '#008700', 'SR_B4': '#c50003', 'SR_B5': '#af54ff',
    'SR_B6': '#ffaf25', 'SR_B7': '#b87e1a',
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
wavebandMapping = {'B': 'SR_B2', 'G': 'SR_B3', 'R': 'SR_B4', 'N': 'SR_B5', 'S1': 'SR_B6', 'S2': 'SR_B7', 'T1': 'SR_B10'}
