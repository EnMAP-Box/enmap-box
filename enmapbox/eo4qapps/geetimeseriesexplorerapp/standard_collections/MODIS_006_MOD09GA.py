collection = ee.ImageCollection("MODIS/006/MOD09GA")

# default colors for bands and spectral indices
bandColors = {
    'sur_refl_b03': '#003fbd',
    'sur_refl_b04': '#008700',
    'sur_refl_b01': '#c50003',
    'sur_refl_b02': '#af54ff',
    'sur_refl_b06': '#ffaf25',
    'sur_refl_b07': '#b87e1a',
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
    'B': 'sur_refl_b03',
    'G': 'sur_refl_b04',
    'R': 'sur_refl_b01',
    'N': 'sur_refl_b02',
    'S1': 'sur_refl_b06',
    'S2': 'sur_refl_b07'
}
