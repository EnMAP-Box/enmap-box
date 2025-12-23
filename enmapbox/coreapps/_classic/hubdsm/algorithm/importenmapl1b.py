from os.path import basename, exists
from typing import Tuple

from osgeo import gdal


def importEnmapL1B(
        filenameMetadataXml: str, filenameVnir: str = None, filenameSwir: str = None
) -> Tuple[gdal.Dataset, gdal.Dataset]:
    '''Return VNIR and SWIR VRT datasets with spectral information (wavelength and FWHM) and data gains/offsets.'''

    assert isEnmapL1BProduct(filenameMetadataXml=filenameMetadataXml)

    if filenameVnir is None:
        filenameVnir = filenameMetadataXml.replace('METADATA.XML', 'EnMAP-Box_VNIR.vrt')
    if filenameSwir is None:
        filenameSwir = filenameMetadataXml.replace('METADATA.XML', 'EnMAP-Box_SWIR.vrt')
    assert isinstance(filenameMetadataXml, str)
    assert isinstance(filenameVnir, str)
    assert isinstance(filenameSwir, str)
    assert filenameVnir.lower().endswith('.vrt')
    assert filenameSwir.lower().endswith('.vrt')

    # read metadata
    import xml.etree.ElementTree as ET
    root = ET.parse(filenameMetadataXml).getroot()
    wavelength = [item.text for item in root.findall('specific/bandCharacterisation/bandID/wavelengthCenterOfBand')]
    fwhm = [item.text for item in root.findall('specific/bandCharacterisation/bandID/FWHMOfBand')]
    gains = [item.text for item in root.findall('specific/bandCharacterisation/bandID/GainOfBand')]
    offsets = [item.text for item in root.findall('specific/bandCharacterisation/bandID/OffsetOfBand')]

    # create VRTs
    filename = filenameMetadataXml.replace('-METADATA.XML', '-SPECTRAL_IMAGE_VNIR.TIF')
    assert exists(filename)
    ds = gdal.Open(filename)
    options = gdal.TranslateOptions(format='VRT')
    dsVnir: gdal.Dataset = gdal.Translate(destName=filenameVnir, srcDS=ds, options=options)
    dsVnir.SetMetadataItem('wavelength', '{'+', '.join(wavelength[:dsVnir.RasterCount]) + '}', 'ENVI')
    dsVnir.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
    dsVnir.SetMetadataItem('fwhm', '{'+', '.join(fwhm[:dsVnir.RasterCount]) + '}', 'ENVI')

    filename = filenameMetadataXml.replace('-METADATA.XML', '-SPECTRAL_IMAGE_SWIR.TIF')
    assert exists(filename)
    ds = gdal.Open(filename)
    options = gdal.TranslateOptions(format='VRT')
    dsSwir: gdal.Dataset = gdal.Translate(destName=filenameSwir, srcDS=ds, options=options)
    dsSwir.SetMetadataItem('wavelength', '{'+', '.join(wavelength[dsVnir.RasterCount:]) + '}', 'ENVI')
    dsSwir.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
    dsSwir.SetMetadataItem('fwhm', '{'+', '.join(fwhm[dsVnir.RasterCount:]) + '}', 'ENVI')

    rasterBands = list()
    rasterBands.extend(dsVnir.GetRasterBand(i+1) for i in range(dsVnir.RasterCount))
    rasterBands.extend(dsSwir.GetRasterBand(i+1) for i in range(dsSwir.RasterCount))
    rasterBand: gdal.Band
    for i, rasterBand in enumerate(rasterBands):
        rasterBand.SetScale(float(gains[i]))
        rasterBand.SetOffset(float(offsets[i]))
        rasterBand.FlushCache()

    # fix wrong GeoTransform tuple
    geoTransform = dsVnir.GetGeoTransform()
    geoTransform = geoTransform[:-1] + (-abs(geoTransform[-1]), )
    dsVnir.SetGeoTransform(geoTransform)
    geoTransform = dsSwir.GetGeoTransform()
    geoTransform = geoTransform[:-1] + (-abs(geoTransform[-1]), )
    dsSwir.SetGeoTransform(geoTransform)

    return dsVnir, dsSwir

def isEnmapL1BProduct(filenameMetadataXml: str):
    # r'ENMAP01-____L1B-DT000000987_20130205T105307Z_001_V000101_20190426T143700Z__rows100-199\ENMAP01-____L1B-DT000000987_20130205T105307Z_001_V000101_20190426T143700Z-METADATA.XML'
    basename_ = basename(filenameMetadataXml)
    valid = True
    valid &= basename_.startswith('ENMAP')
    valid &= 'L1B' in basename_
    valid &= basename_.endswith('METADATA.XML')
    return valid
