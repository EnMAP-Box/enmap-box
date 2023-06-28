# -*- coding: utf-8 -*-
import numpy as np
from enmapbox.coreapps._classic.hubflow.core import *
from osgeo import gdal
# Zone Martin:
import time
import csv
import pandas as pd


stringtext = "tts=42.0;45.0"
stringtext = stringtext.split("=")[1].split(";")
tto_LUT = [float(angle) for angle in stringtext]
print(tto_LUT)

exit()


file = r"E:\Dokumente und Einstellungen\User_Martin\Eigene Dateien\TextDokumente\Beruf\Uni\Homeoffice\EnMAP\SRF\srf_enmap\band001.rsp"

# sniff dialect
sniffer = csv.Sniffer()
all_lines = list()
with open(file, 'r') as raw_file:
    dialect = sniffer.sniff(raw_file.readline())
    delimiter = dialect.delimiter
    raw_file.seek(0)
    # raw = csv.reader(raw_file, dialect)
    raw = csv.reader(raw_file, delimiter=delimiter)
    for line in raw:
        all_lines.append([i for i in line if i])

try:
    _ = [float(i) for i in all_lines[0]]
    header_bool = False
    skiprow = 0
except ValueError:
    header_bool = True
    skiprow = 1

try:
    wl_testing = all_lines[1][0]
    if float(wl_testing) < 1:
        wl_convert = 1  # presumably µm
    else:
        wl_convert = 1000  # presumably nm
except ValueError:
    pass

weights = [float(all_lines[i][0]) for i in range(skiprow, len(all_lines))]
wavelengths = [float(all_lines[i][1]) for i in range(skiprow, len(all_lines))]

if header_bool:
    header_items = all_lines[0]

srf_df = None
single_filename = os.path.basename(file)



if header_bool:
    try:
        header_df = pd.read_csv(file, delimiter=delimiter, header=None,
                                index_col=False, nrows=1)
        header_items = list(header_df.iloc[0, :].dropna())
    except pd.errors.ParserError:
        exit("Error reading header from file {}".format(single_filename))

    if not len(header_items) == 2:
        exit("Error at file {}: Header has {:d} columns. Number of columns " \
                      "expected is 2 (wavelengths and weights)".format(single_filename, len(header_items)))
        skiprows = 1
    else:
        skiprows = 0
    try:
        df = pd.read_csv(file, delimiter=delimiter, header=None, skiprows=skiprows, index_col=False)
    except pd.errors.ParserError:
        exit("Error reading file {}".format(single_filename))

    print(df)
    exit()

    df = df.dropna(how='all', axis=1)
    header_items = ['(band {:00d}) wavelengths'.format(1), 'weights']  # create new header names

    if not len(df.columns) == 2:
        exit("Error at file {}: Data has {:d} columns. Number of columns " \
                      "expected is 2 (wavelengths and weights)".format(single_filename, len(df.columns)))
    df.columns = header_items  # place new header

    try:
        df = df.astype(float)
    except ValueError:
        exit("Error: Cannot read file {}. Please check delimiter (and header)!".format(single_filename))

    if srf_df is None:  # first run of the iteration, srf_df is still empty
        srf_df = df.copy(deep=True)
    else:
        srf_df = pd.concat([srf_df, df], axis=1)  # join df of current file with existing srf_df along columns
print(header_items)

exit()

ImgIn = r"F:\Umweltfernerkundung\Hyperspektral\2009_HyMap/2009_Neusling_EnMAP.bsq"
ImgOut = r"F:\Umweltfernerkundung\Hyperspektral\2009_HyMap/2009_Neusling_EnMAP_compressed.bsq"

dataset = openRasterDataset(ImgIn)
in_matrix = dataset.readAsArray().astype(dtype=np.int16)

grid = dataset.grid()
nbands, nrows, ncols = in_matrix.shape

delete_bands = list(range(4)) + list(range(78, 88)) + [128] + list(range(170, 181))
out_matrix = np.delete(in_matrix, delete_bands, axis=0).astype(dtype=np.int16)

wavelengths = dataset.metadataItem(key='wavelength', domain='ENVI')
wavelengths_out = [wavelengths[i] for i in range(len(wavelengths)) if not i in delete_bands]

driver = gdal.GetDriverByName('ENVI')
output = RasterDataset.fromArray(array=out_matrix, filename=ImgOut, grid=grid, driver=EnviDriver())
output.setMetadataItem('data ignore value', -999, 'ENVI')
output.setMetadataItem('wavelength', wavelengths_out, 'ENVI')
output.setMetadataItem('wavelength_units', 'nanometers', 'ENVI')

for iband, band in enumerate(output.bands()):
    band.setNoDataValue(-999)

exit()

# ImgIn = r"F:\Umweltfernerkundung\Hyperspektral\Regression/sample40.bsq"
ImgIn = r"F:\Umweltfernerkundung\Hyperspektral\2009_HyMap/2009_Neusling_EnMAP.bsq"
ImgOut = r"F:\Umweltfernerkundung\Hyperspektral\2009_HyMap/2009_Neusling_EnMAP_subset.bsq"

dataset = openRasterDataset(ImgIn)
in_matrix = dataset.readAsArray().astype(dtype=np.int32)
grid = dataset.grid()

nbands, nrows, ncols = in_matrix.shape
# dataset = gdal.Open(ImgIn)
# nrows = dataset.RasterYSize
# ncols = dataset.RasterXSize
# nbands = dataset.RasterCount
driver = gdal.GetDriverByName('ENVI')
# proj = dataset.GetProjection()
# grid = dataset.grid()

# in_matrix = dataset.ReadAsArray()
out_matrix = in_matrix[:, 1240:1851, 510:991]

output = RasterDataset.fromArray(array=out_matrix, filename=ImgOut, driver=EnviDriver())
output.setMetadataItem('data ignore value', -999, 'ENVI')

for iband, band in enumerate(output.bands()):
    band.setNoDataValue(-999)

exit()

output = RasterDataset.fromArray(array=out_matrix, filename=ImgOut, grid=grid,
                                 driver=driver)
output.setMetadataItem('data ignore value', self.m.proc_main.nodat[1], 'ENVI')

for iband, band in enumerate(output.bands()):
    band.setDescription(paras_out[iband])
    band.setNoDataValue(self.m.proc_main.nodat[1])
else:
    for ipara in range(len(paras_out)):
        image_out_individual = image_out[:-4] + "_" + paras_out[ipara] + image_out[-4:]
        output = RasterDataset.fromArray(array=out_matrix[ipara, :, :], filename=image_out_individual, grid=grid,
                                         driver=EnviDriver())
        output.setMetadataItem('data ignore value', self.m.proc_main.nodat[1], 'ENVI')
        band = next(output.bands())  # output.bands() is a generator; here only one band
        band.setDescription(paras_out[ipara])
        band.setNoDataValue(self.m.proc_main.nodat[1])


exit()

with open(file, 'r') as meta_file:
    content = meta_file.readlines()
    content = [item.rstrip("\n") for item in content]
keys, values = list(), list()
[[x.append(y) for x, y in zip([keys, values], line.split(sep="=", maxsplit=1))] for line in content]
values = [value.split(';') if ';' in value else value for value in values]

meta_dict = dict(zip(keys, values))
print(meta_dict['alg'])
exit()

SRF_File = np.load(r'/lmuvegetationapps/Resources/srf\Sentinel2.srf')
srf = SRF_File['srf']
srf_nbands = SRF_File['srf_nbands']
wl_sensor = SRF_File['sensor_wl']
n_wl_sensor = len(wl_sensor)
# self.fwhm = SRF_File['sensor_fwhm']  # deprecated
ndvi = SRF_File['sensor_ndvi']

print("Stop")


exit()

sample_size = 50000
LUT_size = 2000
n_features = 10

mydata_array = np.random.uniform(low=0, high=1500, size=(n_features, sample_size))
myLUT = np.random.uniform(low=0, high=1500, size=(n_features, LUT_size))

start = time.time()
result = np.zeros(shape=(sample_size, n_features))
for isample in range(sample_size):
    mydata = mydata_array[:, isample]  # Get current sample
    delta = np.sum(np.abs(mydata[:, np.newaxis] - myLUT), axis=0)
    L1_subset = np.argpartition(delta, 50)[:50]  # get n best performing LUT-entries
    L1_subset = L1_subset[np.argsort(delta[L1_subset])]
    result[isample, :] = np.median(myLUT[:, L1_subset], axis=1)
    if isample % 100 == 0:
        print("Finished {:d} of {:d} samples; took {:.5f} seconds so far!".format(isample, sample_size, time.time()-start))

print("Calculation took {:6.5f} seconds".format(time.time() - start))

exit()

import joblib

### Tiling
raster = openRasterDataset(filename=enmapboxtestdata.enmap)

result = MemDriver().create(grid=raster.grid(),
                            bands=raster.zsize(),
                            gdalType=gdal.GDT_Float32)

for subgrid, i, iy, ix in raster.grid().subgrids(size=256):

    array = raster.array(grid=subgrid)
    result.writeArray(array=array, grid=subgrid)

###
exit()


w4ter_absorption_bands = list()
last = -2
start = -1

for item in flat_list:
    if item != last+1:
        if start != -1:
            w4ter_absorption_bands.append(range(start, last + 1))
            # p.append([start, last])
        start = item
    last = item

w4ter_absorption_bands.append(range(start, last+1))

print(flat_list)
print(w4ter_absorption_bands)