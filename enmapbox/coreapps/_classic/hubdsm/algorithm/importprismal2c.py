from os.path import basename, exists

import numpy as np

from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsRectangle, QgsCoordinateReferenceSystem

from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.resolution import Resolution
from _classic.hubdsm.core.size import Size


def importPrismaL2C(filenameHe5: str, filenameSpectral: str = None) -> gdal.Dataset:
    '''Return raster with correct interleave and spectral information (wavelength and FWHM).'''

    assert isPrismaL2CProduct(filenameHe5=filenameHe5)
    assert isinstance(filenameHe5, str)
    if filenameSpectral is None:
        filenameSpectral = filenameHe5.replace('.he5', '.tif')
    assert isinstance(filenameSpectral, str)

    ds: gdal.Dataset = gdal.Open(filenameHe5)
    filenameLatitude = ds.GetSubDatasets()[1][0]
    assert filenameLatitude.endswith('Latitude')
    filenameSwir = ds.GetSubDatasets()[13][0]
    assert filenameSwir.endswith('SWIR_Cube')
    filenameVnir = ds.GetSubDatasets()[15][0]
    assert filenameVnir.endswith('VNIR_Cube')

    layer = QgsRasterLayer(filenameLatitude)
    layerExtent: QgsRectangle = layer.extent()
    size = Size(x=layerExtent.xMaximum()-layerExtent.xMinimum(), y=layerExtent.yMaximum()-layerExtent.yMinimum())
    resolution=Resolution(x=size.x / 1000, y=size.y / 1000)
    grid = Grid(
        extent=Extent(ul= Location(x=layerExtent.xMinimum(), y=layerExtent.yMaximum()), size=size),
        resolution=resolution,
        projection=Projection.fromEpsg(4326)
    )

    arrayVnir = gdal.Open(filenameVnir).ReadAsArray()
    arraySwir = gdal.Open(filenameSwir).ReadAsArray()
    array = np.vstack((np.transpose(arrayVnir, [1,0,2]), np.transpose(arraySwir, [1,0,2])))
    Raster.createFromArray(array=array, grid=grid, filename=filenameSpectral)
#    r = Raster.open(filenameLatitude)


    assert 0
    #r'HDF5:"C:\Users\janzandr\Downloads\PRS_L2C_STD_20200209102459_20200209102503_0001\PRS_L2C_STD_20200209102459_20200209102503_0001.he5"://HDFEOS/SWATHS/PRS_L2C_AEX/Geolocation_Fields/Latitude'

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


def isPrismaL2CProduct(filenameHe5: str):
    # r'PRS_L2C_STD_20200209102459_20200209102503_0001.he5'
    basename_ = basename(filenameHe5)
    valid = True
    valid &= basename_.startswith('PRS_L2C')
    valid &= basename_.endswith('.he5')
    return valid
