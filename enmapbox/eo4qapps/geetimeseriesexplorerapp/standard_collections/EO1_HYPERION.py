collection = ee.ImageCollection("EO1/HYPERION")

# default colors for bands and spectral indices
bandColors = {
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
wavebandMapping = {'A': 'B010', 'B': 'B014', 'G': 'B021', 'R': 'B031', 'RE1': 'B035', 'RE2': 'B039', 'RE3': 'B043',
                   'RE4': 'B051', 'N': 'B048', 'S1': 'B147', 'S2': 'B205'}
