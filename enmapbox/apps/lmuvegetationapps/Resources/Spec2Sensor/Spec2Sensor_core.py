# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Inversion_core.py - LMU Agri Apps - Artificial Neural Network based spectroscopic image inversion of
    PROSAIL parameters - GUI
    -----------------------------------------------------------------------
    begin                : 09/2020
    copyright            : (C) 2020 Martin Danner; Matthias Wocher
    email                : m.wocher@lmu.de

***************************************************************************
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.
                                                                                                                                                 *
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software. If not, see <http://www.gnu.org/licenses/>.
***************************************************************************

This module handles the conversion between sensors, mostly in terms of spectral downsampling to the characteristics
of the "target sensor". It was originally designed to obtain pseudo-EnMAP spectra from ASD FieldSpec reflectances
-> 400-2500nm @ 1nm ==> 242 EnMAP bands; without altering the spatial resolution or performing any other radiometric
processing.

There are two classes: one performs the conversion when the spectral response function (SRF) is already there in
the form of numpy files with .srf extension. These .srf-files can only be read by THIS module, they are not
standardized in any form! They are just binary files containing the weights associated with wavelengths for all
bands of the target sensor.
The other class is designed to create these .srf-files from text-based information about weights and wavelengths
in a certain structure which was introduced by Karl Segl for dealing with the EnMAP-end-to-end-simulator (EeteS).

The general concept of a spectral response function is that each band of the target sensor carries information not
only about its central wavelength but also about adjacent wavelengths. For example, EnMAP band 17 @ 503 nm is made up
from wavelengths 492 nm with weight 0.0001, 493 nm with weight 0.0003, 494 nm with weight 0.0014, ... 502 nm with
weight 0.922, 503 nm with weight 1.0, 504 nm with weight 0.922, ... 514 nm with weight 0.0001. Each band of the target
sensor has its own text file which needs to have two columns: wavelengths and weights. Additionally, the central
wavelengths of the target sensors need to be known, as they cannot be extracted from the weights right away. It can
be single column (wavelengths) or two columns (wavelengths & FWHM).
"""



import numpy as np
import csv
import os
from enmapbox.coreapps._classic.hubflow.core import *


# Execution of a conversion between two sensors
class Spec2Sensor:
    
    def __init__(self, nodat, sensor):
        self.wl_sensor, self.fwhm = (None, None)
        self.wl = range(400, 2501)
        self.n_wl = len(self.wl)
        self.nodat = nodat
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.sensor = sensor

    def init_sensor(self):
        # Initialize values for the sensor
        try:
            srf_file = np.load(self.path + "/srf/" + self.sensor + ".srf")
        except FileNotFoundError:
            print("File {} not found, please check directories!".format(self.sensor + ".srf"))
            return False

        # the srf file is a numpy .npz; this file type contains more than one array and are addressed by name like
        # dictionaries from the np.open object
        self.srf = srf_file['srf']
        self.srf_nbands = srf_file['srf_nbands']
        self.wl_sensor = srf_file['sensor_wl']
        self.n_wl_sensor = len(self.wl_sensor)
        if 'sensor_fwhm' in srf_file:
            self.fwhm = srf_file['sensor_fwhm']  # deprecated
        else:
            self.fwhm = None
        # self.fwhm = srf_file['sensor_fwhm']  # deprecated
        self.ndvi = srf_file['sensor_ndvi']
        return True  # return True if everything worked

    def run_srf(self, reflectance, int_factor_wl=1000):
        # convert reflectances to new sensor; the function is vectorized and takes arrays of reflectances
        hash_getwl = dict(zip(self.wl, list(range(self.n_wl))))  # dictionary to map wavelengths [nm] to wavebands
        spec_corr = np.zeros(shape=(reflectance.shape[0], self.n_wl_sensor))  # prepare array for corrected refs

        for sensor_band in range(self.n_wl_sensor):  # for each band of the target sensor
            wfactor_include = list()  # empty the list of wfactors to include in the weighting function
            for srf_i in range(self.srf_nbands[sensor_band]):  # for each srf_value of the band
                try:
                    # obtain wavelength of for the band and srf_i value ([0]) and boost with the int_factor
                    wlambda = int(self.srf[srf_i][sensor_band][0] * int_factor_wl)
                except ValueError:
                    print("Error with sensor band {:d} at the srf #{:d}".format(sensor_band, srf_i))
                    return

                if wlambda not in self.wl:  # this happens when a wavelength is specified
                    continue                # in the srf-file outside 400-2500

                # Do the same with the weighting factor for band and srf_i value ([1])
                wfactor = self.srf[srf_i][sensor_band][1]
                wfactor_include.append(srf_i)  # add it to the list of wfactors for this sensor band
                # add to the spectral sums for this sensor band
                spec_corr[:, sensor_band] += reflectance[:, hash_getwl[wlambda]] * wfactor
                pass

            # get the total sum for the sensor band
            sum_wfactor = sum(self.srf[i][sensor_band][1] for i in wfactor_include)

            try:
                spec_corr[:, sensor_band] /= sum_wfactor  # divide by the sum to get a weighted average
            except ZeroDivisionError:  # this happens when no srf-value can be extracted from the original data
                spec_corr[:, sensor_band] = self.nodat

        return spec_corr

    def convert_image(self, in_file, out_file, nodat):
        # Method to convert a whole image from one sensor to another
        dataset = openRasterDataset(in_file)
        in_matrix = dataset.readAsArray()
        nbands, nrows, ncols = in_matrix.shape
        grid = dataset.grid()

        metadict = dataset.metadataDict()
        print(metadict)
        wavelengths = metadict['ENVI']['wavelength']
        wl_units = metadict['ENVI']['wavelength units']
        if wl_units.lower() in ['nanometers', 'nm', 'nanometer']:  # any of these is accepted
            wave_convert = 1  # factor is 1, as the method expects nm anyway
        elif wl_units.lower() in ['micrometers', 'µm', 'micrometer']:
            wave_convert = 1000  # factor is 1000 to obtain nm
        else:
            exit()

        # Be aware that wavelengths are converted into int, so 423.89 nm will become 423 nm.
        self.wl = np.asarray([float(wl * wave_convert) for wl in wavelengths])
        self.n_wl = self.wl.shape[0]

        reflectances_straight = np.swapaxes(np.reshape(in_matrix, (nbands, -1)), 0, 1)
        result = self.run_srf(reflectance=reflectances_straight, int_factor_wl=1000)
        out_matrix = np.reshape(np.swapaxes(result, 0, 1), (self.n_wl_sensor, nrows, ncols))
        out_matrix = out_matrix.astype(np.int16)

        output = RasterDataset.fromArray(array=out_matrix, filename=out_file, grid=grid,
                                         driver=EnviDriver())

        output.setMetadataItem('data ignore value', nodat, 'ENVI')
        output.setMetadataItem('wavelength', "{" + ", ".join(str(i) for i in self.wl_sensor) + "}", 'ENVI')
        output.setMetadataItem('wavelength units', "Nanometers", 'ENVI')
        output.setMetadataItem('fwhm', "{" + ", ".join(str(i) for i in self.fwhm) + "}", 'ENVI')

        for iband, band in enumerate(output.bands()):
            band.setDescription("Band {:00d}".format(iband))
            band.setNoDataValue(nodat)


# This class builds new srf-files (numpy) from text files with the ideal structure of K. Segl's files
class BuildTrueSRF:

    def __init__(self, srf_files, wl_file=None, out_file=None, delimiter=None,
                 header_bool=None, wl_convert=None, nodat=-999):
        self.files = srf_files
        self.wl_file = wl_file
        self.out_file = out_file
        self.delimiter = delimiter
        self.header_bool = header_bool
        self.wl_convert = wl_convert
        self.nodat = nodat

    def dframe_from_txt(self):
        # This function reads the text files with srf-content and returns the actual data in the right format

        # "sniff" the dialect of the text file (delimiter and presence of header)
        sniffer = csv.Sniffer()
        with open(self.files[0], 'r') as raw_file:  # open just the first file and hope, they are all identical
            if not self.delimiter:  # if the delimiter is not known before and passed to the class instance...
                dialect = sniffer.sniff(raw_file.readline())
                self.delimiter = dialect.delimiter
            raw_file.seek(0)  # rewind file
            raw = csv.reader(raw_file, delimiter=self.delimiter)
            try:
                firstline = [i for i in next(raw) if i]   # removes blank columns in K. Segl SRF files
                secondline = [i for i in next(raw) if i]   # - " -
            except ImportError("Files could not be read."):
                return False

            if not self.header_bool:  # header is False by default (which means "not known")
                try:
                    # if at least one item in the first line cannot be converted to float, we treat this as a header
                    _ = [float(i) for i in firstline]
                    self.header_bool = False
                except ValueError:
                    self.header_bool = True

            if not self.wl_convert:   # SRF must be stored in µm; that's awkward but it's the standard I'm afraid
                try:
                    wl_testing = secondline[0]
                    if float(wl_testing) < 1:  # we ignore the possibility that the unit is cm or mm
                        self.wl_convert = 1  # presumably µm
                    else:
                        self.wl_convert = 1000  # presumably nm
                except ValueError:
                    pass

        srf_list = list()
        for i_file, single_file in enumerate(self.files):   # iterate through all the files (1 file = 1 target band)
            single_filename = os.path.basename(single_file)
            all_lines = list()
            with open(single_file, 'r') as raw_file:
                raw = csv.reader(raw_file, delimiter=self.delimiter)
                for line in raw:
                    all_lines.append([i for i in line if i])  # all_lines contains all rows of data as items of a list
            if self.header_bool:
                header_items = all_lines[0]
                if not len(header_items) == 2:
                    return False, "Error at file {}: Header has {:d} columns. Number of columns " \
                                  "expected is 2 (wavelengths and weights)".format(single_filename, len(header_items))
                skiprows = 1
            else:
                skiprows = 0
                # # create new header names: deprecated! This is now handled by whatever GUI is calling this method
                # header_items = ['(band {:00d}) wavelengths'.format(i_file + 1), 'weights']

            try:
                # convert all data (wavelengths and weights) from string to float
                wavelengths = [float(all_lines[i][0]) for i in range(skiprows, len(all_lines))]
                weights = [float(all_lines[i][1]) for i in range(skiprows, len(all_lines))]
            except ValueError:
                return False, "Error interpreting content of '{}' as decimals!".format(single_filename)

            if not len(all_lines[1]) == 2:
                return False, "Error at file {}: Data has {:d} columns. Number of columns " \
                              "expected is 2 (wavelengths and weights)".format(single_filename, len(all_lines[1]))

            # List-dimensions of 'srf_list': [Band target sensor][[0: wavelengths, 1: weights][values]
            srf_list.append([wavelengths, weights])

        return True, srf_list

    def srf_from_dframe(self, srf_list):
        # This function builds the srf-numpy files from the information of dframe_from_txt
        # Some notes on this: most of the bands of the target sensor have a different length of adjacent wavelengths
        # that influence the weighted sums. For example, EnMAP band 17 considers 23 adjacent bands, band 42 considers
        # 29 adjacent bands. The srf wavelengths and weights are stored in numpy arrays which cannot have different
        # lengths along their axes. For this reason, the band with the most srf-values defines the shape of the array
        # and all shorter bands are filled with "NoData" values

        nbands_sensor = len(srf_list)  # how many bands in the target sensor?
        srf_nbands = [len(srf_list[i][0]) for i in range(nbands_sensor)]  # how many srf-values per band of the sensor?

        # The band with the most srf-values defines dim0 of the output array, the rest is filled with nodata values
        # the "2" in dim2: [0] is wavelengths, [1] is weights.
        new_srf = np.full(shape=(np.max(srf_nbands), nbands_sensor, 2), fill_value=self.nodat, dtype=np.float64)

        # Mind the conversion of the wavelengths into µm! Broadcast the data into the array
        for band in range(nbands_sensor):
            new_srf[0:srf_nbands[band], band, 0] = np.asarray(srf_list[band][0][:srf_nbands[band]]) / self.wl_convert
            new_srf[0:srf_nbands[band], band, 1] = np.asarray(srf_list[band][1][:srf_nbands[band]])

        try:
            # Load the information about central wavelengths of the target sensor from the given file
            wavelength = np.loadtxt(self.wl_file) / self.wl_convert
        except:
            return False, "Error reading wavelength file! Expected text-file with one float-value " \
                          "per line (i.e. wavelength)"

        # What happens when there are more wavelengths given than in the SRF files?
        if not wavelength.shape[0] == nbands_sensor:
            return False, "Got {:d} bands in wavelength-file, but {:d} bands in SRF-File!"\
                .format(int(wavelength.shape[0]), nbands_sensor)

        # Store information about which bands should be used for
        # calculating the NDVI in the srf-Numpy file (some tools need this!)
        ndvi = list()
        ndvi.append(np.argmin(np.abs(wavelength - 0.677)))  # find band that is closest to "red"
        ndvi.append(np.argmin(np.abs(wavelength - 0.837)))  # find band that is closest to "nir"

        # np.savez (unlike np.save) saves multiple arrays to a file; the arguments are stored and serve as keys
        # to access the data just like a dictionary: bla = np.load(file); print(bla['sensor_ndvi'])
        np.savez(self.out_file, srf_nbands=srf_nbands, srf=new_srf, sensor_wl=wavelength, sensor_ndvi=ndvi)
        os.rename(self.out_file, os.path.splitext(self.out_file)[0] + ".srf")  # rename from .npz to .srf

        # returning the filename helps with putting the correct name into the combobox
        return True, os.path.splitext(os.path.basename(self.out_file))[0]


class BuildGenericSRF:

    def __init__(self, imagery, out_file=None, wl_convert=None, nodat=-999):
        self.image = imagery
        self.out_file = out_file
        self.wl_convert = wl_convert
        self.nodat = nodat

    def srf_from_imagery(self, x):   # fwhm-style
        wavelength = x[:, 0]
        fwhm = x[:, 1]
        # sigma = fwhm / 2.355  # temporarily disabled
        x_list = list()
        gs_list = list()

        for wl in range(len(wavelength)):
            x_lower = scipy.stats.norm.ppf(0.105, wavelength[wl], fwhm[wl])
            x_upper = scipy.stats.norm.ppf(0.895, wavelength[wl], fwhm[wl])

            x = np.arange(x_lower, x_upper+1)
            gs = scipy.stats.norm.pdf(x, wavelength[wl], fwhm[wl])
            x_list.append(x)
            gs_list.append(gs)

        for ix, x in enumerate(x_list):
            n_invalid = sum(i > 2500 or i < 400 for i in x)  # if outreach of PDF is beyond PROSAIL range, then clip on both sides
            if n_invalid > 0:
                x_list[ix] = x_list[ix][n_invalid:-n_invalid]
                gs_list[ix] = gs_list[ix][n_invalid:-n_invalid]

        new_srf_nbands = np.asarray([len(i) for i in x_list])
        new_srf = np.full(shape=(np.max(new_srf_nbands), len(wavelength), 2), fill_value=self.nodat, dtype=np.float64)

        for wl in range(len(wavelength)):
            new_srf[0:new_srf_nbands[wl], wl, 0] = np.around(x_list[wl]/1000, decimals=4)
            new_srf[0:new_srf_nbands[wl], wl, 1] = gs_list[wl]

        ndvi = list()
        ndvi.append(np.argmin(np.abs(wavelength - 677)))  # red
        ndvi.append(np.argmin(np.abs(wavelength - 837)))  # nir

        np.savez(self.out_file, srf_nbands=new_srf_nbands, srf=new_srf, sensor_wl=wavelength, sensor_ndvi=ndvi, sensor_fwhm=fwhm) #sensor_fwhm added
        os.replace(self.out_file, os.path.splitext(self.out_file)[0] + ".srf")

        return True, self.out_file, os.path.splitext(os.path.basename(self.out_file))[0]
        #return filename  # returning the filename helps with putting the correct name into the combobox
