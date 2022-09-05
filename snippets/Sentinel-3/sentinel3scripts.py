import os
import pathlib
import re
from osgeo import gdal
from qgis.core import QgsApplication

#  ########### CONFIG SECTION ################
# Ordner mit entpacken Sentinel-3 L1 Datensätzen:
dirS3_L1 = r'D:\Temp\Sentinel-3\S3A_OL_1_EFR____20201008T234915_20201008T235215_20201010T044927_0179_063_344_1980_LN1_O_NT_002.SEN3'

#  ############################################

dirS3_L1 = pathlib.Path(dirS3_L1)
assert dirS3_L1.is_dir(), f'Ordner existiert nicht: {dirS3_L1}'

pathXML = dirS3_L1 / 'geo_coordinates.nc'

ds = gdal.Open(pathXML.as_posix())

# wavelength:
S3_OLCI_Wavelengths = [
    400.0, 412.50, 442.50, 490.00, 510.00, 560.00, 620.00, 665.00, 673.75, 681.25, 708.75, 753.75, 761.25, 764.375,
    767.50, 778.75, 865.00, 885.00, 900.00, 940.00, 1020.00]

regex = re.compile(r'\d{2}_radiance\.nc$')
radiance_bands = [p.path for p in os.scandir(dirS3_L1) if regex.search(p.name)]
radiance_bands = sorted(radiance_bands)

pathVRT = dirS3_L1 / 'all_radiance_bands.vrt'
options = gdal.BuildVRTOptions(separate=True)
dsVRT: gdal.Dataset = gdal.BuildVRT(pathVRT.as_posix(), radiance_bands, options=options)

assert dsVRT.RasterCount == len(S3_OLCI_Wavelengths)

dsVRT.SetGeoTransform([0.0, 1.0, 0.0, float(dsVRT.RasterYSize), 0.0, -1.0])  # let the image look north-up
dsVRT.SetMetadataItem('wavelength', ','.join([f'{v}' for v in S3_OLCI_Wavelengths]))
dsVRT.SetMetadataItem('wavelength units', 'nm')

for b, path in enumerate(radiance_bands):
    band: gdal.Band = dsVRT.GetRasterBand(b + 1)
    band.SetDescription(os.path.basename(path))

dsVRT.FlushCache()

if QgsApplication.instance():
    # open in QGIS
    from qgis.core import QgsProject, QgsRasterLayer

    lyr = QgsRasterLayer(pathVRT.as_posix(), pathVRT.name)
    QgsProject.instance().addMapLayer(lyr)
