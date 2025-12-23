from os.path import basename, exists

from osgeo import gdal


def importDesisL2A(filenameMetadataXml: str, filenameSpectral: str = None) -> gdal.Dataset:
    '''Return VRT dataset with spectral information (wavelength and FWHM).'''

    assert isDesisL2AProduct(filenameMetadataXml=filenameMetadataXml)

    if filenameSpectral is None:
        filenameSpectral = filenameMetadataXml.replace('METADATA.xml', 'EnMAP-Box_SPECTRAL.vrt')
    assert isinstance(filenameMetadataXml, str)
    assert isinstance(filenameSpectral, str)
    assert filenameSpectral.lower().endswith('.vrt')

    # read metadata
    filenameEnviHdr = filenameMetadataXml.replace('-METADATA.xml', '-SPECTRAL_IMAGE.hdr')
    with open(filenameEnviHdr) as file:
        text = file.read()
    text = text.replace('  ', ' ')

    def getMetadataList(key, text):
        i1 = text.index(key + ' = {')
        i2 = text.index('}', i1)
        value = text[i1 + len(key) + 3:i2 + 1].replace('\n', '')
        return value

    key = 'wavelength'
    wavelength = getMetadataList(key, text)
    key = 'fwhm'
    fwhm = getMetadataList(key, text)

    # create VRTs
    filename = filenameMetadataXml.replace('-METADATA.xml', '-SPECTRAL_IMAGE.TIF')
    assert exists(filename)
    ds = gdal.Open(filename)
    bandNames = [ds.GetRasterBand(i + 1).GetDescription() for i in range(ds.RasterCount)]
    options = gdal.TranslateOptions(format='VRT')
    ds: gdal.Dataset = gdal.Translate(destName=filenameSpectral, srcDS=ds, options=options)
    ds.SetMetadataItem('wavelength', wavelength, 'ENVI')
    ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
    ds.SetMetadataItem('fwhm', fwhm, 'ENVI')
    rasterBands = [ds.GetRasterBand(i + 1) for i in range(ds.RasterCount)]
    rasterBand: gdal.Band
    for rasterBand, bandName in zip(rasterBands, bandNames):
        rasterBand.SetDescription(bandName)
    return ds


def isDesisL2AProduct(filenameMetadataXml: str):
    # r'DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210-METADATA.xml'
    basename_ = basename(filenameMetadataXml)
    valid = True
    valid &= basename_.startswith('DESIS-HSI-L2A')
    valid &= basename_.endswith('METADATA.xml')
    return valid
