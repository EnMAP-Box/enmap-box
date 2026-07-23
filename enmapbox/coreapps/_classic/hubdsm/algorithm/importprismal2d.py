from os.path import basename

import numpy as np

from osgeo import gdal

from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.resolution import Resolution
from _classic.hubdsm.core.size import Size


def importPrismaL2D(filenameHe5: str, filenameSpectral: str = None) -> gdal.Dataset:
    '''Return raster with correct interleave and spectral information (wavelength and FWHM).'''

    assert isPrismaL2DProduct(filenameHe5=filenameHe5)
    assert isinstance(filenameHe5, str)
    if filenameSpectral is None:
        filenameSpectral = filenameHe5.replace('.he5', '.tif')
    assert isinstance(filenameSpectral, str)

    ds: gdal.Dataset = gdal.Open(filenameHe5)
    meta = ds.GetMetadata()

    filenameSwir = ds.GetSubDatasets()[0][0]
    assert filenameSwir.endswith('SWIR_Cube')
    filenameVnir = ds.GetSubDatasets()[2][0]
    assert filenameVnir.endswith('VNIR_Cube')

    # read, transpose and scale data
    offsetVnir = np.float32(meta['L2ScaleVnirMin'])
    gainVnir = np.float32((float(meta['L2ScaleVnirMax']) - float(meta['L2ScaleVnirMin'])) / 65535 * 10000)
    selectedVnir = np.array(meta['CNM_VNIR_SELECT'].split(), dtype=np.uint8) == 1
    arrayVnir = offsetVnir + np.transpose(gdal.Open(filenameVnir).ReadAsArray(), [1, 0, 2])[selectedVnir][::-1] * gainVnir
    arrayVnir = arrayVnir.astype(np.int16)
    offsetSwir = np.float32(meta['L2ScaleSwirMin'])
    gainSwir = np.float32((float(meta['L2ScaleSwirMax']) - float(meta['L2ScaleSwirMin'])) / 65535 * 10000)
    selectedSwir = np.array(meta['CNM_SWIR_SELECT'].split(), dtype=np.uint8) == 1
    arraySwir = offsetSwir + np.transpose(gdal.Open(filenameSwir).ReadAsArray(), [1, 0, 2])[selectedSwir][::-1] * gainSwir
    arraySwir = arraySwir.astype(np.int16)
    array = np.vstack([arrayVnir, arraySwir])

    # mask nodata
    mask = np.all(array == 0, axis=0)
    array[:, mask] = -9999

    # prepare spatial extent
    xmin = float(meta['Product_ULcorner_easting']) - 15
    ymax = float(meta['Product_ULcorner_northing']) + 15
    xmax = float(meta['Product_LRcorner_easting']) + 15
    ymin = float(meta['Product_LRcorner_northing']) - 15
    resolution = Resolution(x=30, y=30)
    size = Size(x=resolution.x * array.shape[2], y=resolution.y * array.shape[1])
    grid = Grid(
        extent=Extent(ul=Location(x=xmin, y=ymax), size=size),
        resolution=resolution,
        projection=Projection.fromEpsg(int(meta['Epsg_Code']))
    )

    # write data
    gdalRaster = GdalRaster.createFromArray(array=array, grid=grid, filename=filenameSpectral)

    # set metadata
    wavelengthVnir = list(reversed([v for v, flag in zip(meta['List_Cw_Vnir'].split(), selectedVnir) if flag]))
    wavelengthSwir = list(reversed([v for v, flag in zip(meta['List_Cw_Swir'].split(), selectedSwir) if flag]))
    wavelength = wavelengthVnir + wavelengthSwir
    fwhmVnir = list(reversed([v for v, flag in zip(meta['List_Fwhm_Vnir'].split(), selectedVnir) if flag]))
    fwhmSwir = list(reversed([v for v, flag in zip(meta['List_Fwhm_Swir'].split(), selectedSwir) if flag]))
    fwhm = fwhmVnir + fwhmSwir
    assert len(wavelength) == len(array)
    assert len(fwhm) == len(array)
    gdalRaster.setMetadataItem(key='wavelength', value=wavelength, domain='ENVI')
    gdalRaster.setMetadataItem(key='fwhm', value=fwhm, domain='ENVI')
    gdalRaster.setMetadataItem(key='wavelength_units', value='nanometers', domain='ENVI')
    gdalRaster.setNoDataValue(-9999)
    return gdalRaster.gdalDataset


def isPrismaL2DProduct(filenameHe5: str):
    # r'PRS_L2D_STD_20200327103506_20200327103510_0001.he5'
    basename_ = basename(filenameHe5)
    valid = True
    valid &= basename_.startswith('PRS_L2D')
    valid &= basename_.endswith('.he5')
    return valid
