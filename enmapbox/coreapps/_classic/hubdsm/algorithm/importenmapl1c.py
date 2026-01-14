from os.path import basename, exists

from osgeo import gdal


def importEnmapL1C(filenameMetadataXml: str, filenameSpectral: str = None) -> gdal.Dataset:
    '''Return VRT dataset with spectral information (wavelength and FWHM) and data gains/offsets.'''

    assert isEnmapL1CProduct(filenameMetadataXml=filenameMetadataXml)

    if filenameSpectral is None:
        filenameSpectral = filenameMetadataXml.replace('METADATA.XML', 'EnMAP-Box_SPECTRAL.vrt')
    assert isinstance(filenameMetadataXml, str)
    assert isinstance(filenameSpectral, str)
    assert filenameSpectral.lower().endswith('.vrt')

    # read metadata
    import xml.etree.ElementTree as ET
    root = ET.parse(filenameMetadataXml).getroot()
    wavelength = [item.text for item in root.findall('specific/bandCharacterisation/bandID/wavelengthCenterOfBand')]
    fwhm = [item.text for item in root.findall('specific/bandCharacterisation/bandID/FWHMOfBand')]
    gains = [item.text for item in root.findall('specific/bandCharacterisation/bandID/GainOfBand')]
    offsets = [item.text for item in root.findall('specific/bandCharacterisation/bandID/OffsetOfBand')]

    # create VRTs
    filename = filenameMetadataXml.replace('-METADATA.XML', '-SPECTRAL_IMAGE.TIF')
    assert exists(filename)
    ds = gdal.Open(filename)
    options = gdal.TranslateOptions(format='VRT')
    ds: gdal.Dataset = gdal.Translate(destName=filenameSpectral, srcDS=ds, options=options)
    ds.SetMetadataItem('wavelength', '{' + ', '.join(wavelength[:ds.RasterCount]) + '}', 'ENVI')
    ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
    ds.SetMetadataItem('fwhm', '{' + ', '.join(fwhm[:ds.RasterCount]) + '}', 'ENVI')

    rasterBands = [ds.GetRasterBand(i + 1) for i in range(ds.RasterCount)]
    rasterBand: gdal.Band
    for i, rasterBand in enumerate(rasterBands):
        rasterBand.SetScale(float(gains[i]))
        rasterBand.SetOffset(float(offsets[i]))
        rasterBand.FlushCache()
    return ds


def isEnmapL1CProduct(filenameMetadataXml: str):
    # r'ENMAP01-____L1C-DT000326721_20170626T102020Z_001_V000204_20200406T180016Z-METADATA.XML'
    basename_ = basename(filenameMetadataXml)
    valid = True
    valid &= basename_.startswith('ENMAP')
    valid &= 'L1C' in basename_
    valid &= basename_.endswith('METADATA.XML')
    return valid
