collection = ee.ImageCollection("MODIS/006/MCD43A4")

# default colors for bands and spectral indices
bandColors = {
    'Nadir_Reflectance_Band3': '#003fbd',
    'Nadir_Reflectance_Band4': '#008700',
    'Nadir_Reflectance_Band1': '#c50003',
    'Nadir_Reflectance_Band2': '#af54ff',
    'Nadir_Reflectance_Band6': '#ffaf25',
    'Nadir_Reflectance_Band7': '#b87e1a',
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
    'B': 'Nadir_Reflectance_Band3',
    'G': 'Nadir_Reflectance_Band4',
    'R': 'Nadir_Reflectance_Band1',
    'N': 'Nadir_Reflectance_Band2',
    'S1': 'Nadir_Reflectance_Band6',
    'S2': 'Nadir_Reflectance_Band7'
}
