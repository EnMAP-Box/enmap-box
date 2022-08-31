from _classic.hubdc.core2 import *

def raster(filename, wavelength=None, date=None):
    rasterDataset = openRasterDataset(filename=filename)
    raster = Raster(name=basename(filename), date=None)
    extent = rasterDataset.grid().extent()
    tilingScheme = SingleTileTilingScheme(extent=extent)

    if wavelength is None:
        wavelength = rasterDataset.metadataItem(key='wavelength', domain='ENVI', dtype=float)
        if wavelength is not None:
            units = rasterDataset.metadataItem(key='wavelength units', domain='ENVI', required=True)
            if units.lower() in ['nanometers']:
                pass
            elif units.lower() in ['micrometers']:
                wavelength = [v * 1000. for v in wavelength]
            else:
                raise Exception('unknown wavelength units: {}'.format(units))

    if date is None:
        acquisition_time = wavelength = rasterDataset.metadataItem(key='acquisition time', domain='ENVI')
        # see https://www.harrisgeospatial.com/docs/enviheaderfiles.html#acquisition_time for details
        if acquisition_time is not None:
            date = Date.parse(acquisition_time[:len('YYYY-MM-DD')])

    if wavelength is None:
        wavelength = [None] * rasterDataset.zsize()

    for index, rasterBandDataset in enumerate(rasterDataset.bands()):
        name = rasterBandDataset.description()
        raster.addBand(band=Band(filename=filename, index=index, mask=None, name=name, date=date,
                             wavelength=wavelength[index], geometry=extent, tilingScheme=tilingScheme))

#    raster = raster.updateMask(mask=raster.select(0).not_equal(-9999))
    return raster
