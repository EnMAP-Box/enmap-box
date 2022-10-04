collection = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")

# default colors for bands and spectral indices
bandColors = {
    'SR_B1': '#003fbd', 'SR_B2': '#008700', 'SR_B3': '#c50003', 'SR_B4': '#af54ff', 'SR_B5': '#ffaf25',
    'SR_B7': '#b87e1a',
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
wavebandMapping = {'B': 'SR_B1', 'G': 'SR_B2', 'R': 'SR_B3', 'N': 'SR_B4', 'S1': 'SR_B5', 'S2': 'SR_B7', 'T1': 'SR_B6'}
