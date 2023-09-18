# -*- coding: utf-8 -*-
"""
***************************************************************************
    CreateLUT_core.py - LMU Agri Apps - interactive creation of PROSAIL/PROINFORM look-up-tables - Core
    -----------------------------------------------------------------------
    begin                : 06/2018
    copyright            : (C) 2018 Martin Danner; Matthias Wocher
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
"""

# InvertLUT_core.py is the core application to retrieve biophysical and biochemical information by inverting
# Canopy/Leaf spectra using a PROSAIL Lookup-table (LUT)
# The idea is to browse through all spectra of the LUT, treating it as a library, and detect the spectra with closest
# relation to the measured reflectances; The median of the n-best fits is considered the valid result

from enmapbox.coreapps._classic.hubflow.core import *
from matplotlib import pyplot as plt
import numpy as np


# class RTMInversion is the core class of the inversion
class RTMInversion:

    def __init__(self):
        self.error = None
        self.ctype = 0  # cost function type
        self.nbfits = 0  # number of best fits to invert
        self.noisetype = 0  # 0: off, 1: additive, 2: multiplicative, 3: inverse multiplicative
        self.noiselevel = 0  # std of the noise
        self.nodat = [0] * 3  # 0: input image, 1: geometry image, 2: output image
        # which bands to exclude from the image and which from the LUT
        self.exclude_bands_image, self.exclude_bands_model = (None, None)
        self.wl_image = None  # wavelengths of the sensor used
        self.wl_compare = None  # same as wl_image, but without the excluded bands
        self.n_wl = None
        self.offset = 0
        self.image = None
        self.image_out = None
        # when reflectances of the spectral image and those of the LUT are at different ranges, they need to be boosted
        self.conversion_factor = None

        self.nrows, self.ncols, self.nbands = (None, None, None)
        self.geometry_matrix = None
        self.whichLUT = None
        self.LUT_base = None
        self.exclude_pixels = None
        self.whichpara = None

        # LUT:
        self.ntotal = None  # how many entries in total
        self.ns = None  # how many different parameter variations from the statistical distribution of the LUT
        self.tts_LUT, self.tto_LUT, self.psi_LUT, self.nangles_LUT = (None, None, None, None)

    def inversion_setup(self, image, image_out, LUT_path, ctype, nbfits, nbfits_type, noisetype, noiselevel,
                        wl_image, exclude_bands, out_mode, geo_image=None, geo_fixed=None, spatial_geo=False,
                        nodat=None, mask_image=None):

        self.ctype = ctype
        self.nbfits = nbfits
        self.nbfits_type = nbfits_type
        self.noisetype = noisetype
        self.noiselevel = noiselevel

        if nodat is None:
            self.nodat = [-999] * 3
        else:
            self.nodat = nodat
        self.out_mode = out_mode

        self.image_out = image_out

        self.get_lutmeta(LUT_path)  # get the meta data from the LUT meta-file, afterwards self.npara is available

        # Manage wavelengths of Image and LUT
        # Exclude bands model and wl_compare are offset by PROSAIL paras at the first columns of the LUT-readings
        # wl_compare is the reduced list of wavelengths of the image, with the excluded bands removed
        self.wl_image = wl_image
        self.exclude_bands_image = exclude_bands
        self.exclude_bands_model = list(range(self.npara)) + [i + self.npara for i in self.exclude_bands_image]
        self.wl_compare = [self.wl_image[i] for i in range(len(self.wl_image)) if i not in self.exclude_bands_image]
        self.n_wl = len(self.wl_compare)

        self.nrows, self.ncols, self.nbands, self.grid, self.image = \
            self.read_image(image=image, dtype=np.float16, exclude_bands=self.exclude_bands_image)

        if mask_image is None:  # the mask_image defines pixels to be skipped in the inversion
            self.exclude_pixels = []
            self.mask = None
        else:
            mask_rows, mask_cols, _, _, self.mask = self.read_image(image=mask_image, dtype=np.int8)
            if not self.nrows == mask_rows or not self.ncols == mask_cols:  # dimension mismatch between mask and image
                return "Input Image and Mask Image must have same dimensions! Input Image has [{:d}r, {:d}c], " \
                       "Mask Image has [{:d}r, {:d}c]".format(self.nrows, self.ncols, mask_rows, mask_cols)

        # generate list of LUT-names for each pixel
        if geo_fixed is None:
            geo_fixed = [None] * 3
        self.get_geometry(geo_image=geo_image, geo_fixed=geo_fixed, spatial_geo=spatial_geo)

    def read_image(self, image, dtype=np.float16, exclude_bands=None):
        # read spectral image (can also be geometry image or mask image!)
        dataset = openRasterDataset(image)
        in_matrix = dataset.readAsArray().astype(dtype=dtype)  # read the data
        if exclude_bands is not None:  # if bands are to be excluded from the input image, do so now
            in_matrix = np.delete(in_matrix, exclude_bands, 0)
        nbands, nrows, ncols = in_matrix.shape
        grid = dataset.grid()  # store the grid of the input image for later use

        return nrows, ncols, nbands, grid, in_matrix  # return a tuple back to the last function (type "dtype")

    def get_geometry(self, geo_fixed, geo_image=None, spatial_geo=False):
        # manage the geometry between sun, target and observer
        # There are multiple ways to deal with geometries:

        if geo_image:  # an image is supplied with three bands: SZA, OZA, rAA -> it has the same shape as the spec image
            geometry_raw = self.read_image(geo_image)  # geometry_raw = (nrows, ncols, nbands, grid, in_matrix)
            geometry_data = geometry_raw[-1]  # last item is the actual data
            if not geometry_raw[0] == self.nrows or not geometry_raw[1] == self.ncols:  # check for shape
                raise ValueError("Geometry image and Sensor image do not match")

            # Often, geometry is passed as an image with boost of 100, so SZA ranges from e.g. 0 to 4500 (45°)
            # Find out the range and specify the boost for geometry!
            mean_sza = np.mean(geometry_data[geometry_data > 0])
            int_boost_geo = 10 ** (np.ceil(np.log10(mean_sza)) - 2)  # evaluates as 1 for SZA=45, 100 for SZA=4500, ...
            self.geometry_matrix = geometry_data / int_boost_geo

            # spatial_geo == True -> each pixel receives its own LUT according to the geometry settings
            # spatial_geo == False -> calculate the geometry as mean angles over the whole image
            if not spatial_geo:  # get rid of spatial distribution of geometry (tts, tto, psi) within image
                self.geometry_matrix[self.geometry_matrix == self.nodat[1]] = np.nan
                self.geometry_matrix[0, :, :] = np.nanmean(self.geometry_matrix[0, :, :])
                self.geometry_matrix[1, :, :] = np.nanmean(self.geometry_matrix[1, :, :])
                self.geometry_matrix[2, :, :] = np.nanmean(self.geometry_matrix[2, :, :])

        elif geo_fixed:  # no image is specified, geometry is supplied as fixed values by the user
            self.geometry_matrix = np.empty(shape=(3, self.nrows, self.ncols))  # build an empty array
            self.geometry_matrix.fill(self.nodat[2])  # fill with geometry no-data
            if not any(geo_fixed[i] is None for i in range(len(geo_fixed))):
                try:
                    for angle in range(3):
                        # place fixed values everywhere in the geometry_matrix array
                        self.geometry_matrix[angle, :, :] = geo_fixed[angle]
                except ValueError:
                    raise ValueError("Problem with reading fixed angles")

        # self.whichLUT is an array with shape of the input image; the pixel values set an integer number which
        # identifies the LUT to be used. Notice that the same LUT is calculated for different geometry-constellations
        # and those constellations are numbered as integers according to what is specified in the .lut-meta-file
        self.whichLUT = np.zeros(shape=(self.nrows, self.ncols), dtype=np.int16)

        if self.geo_mode == "sort":  # LUT contains SZA, OZA, rAA with many values (sorted)
            for row in range(self.nrows):
                for col in range(self.ncols):
                    # find the geometrical setting that is closest to the geometry that is actually observed
                    # tts_LUT, tto_LUT and psi_LUT are the constellations present in the LUT
                    angles = list()
                    angles.append(np.argmin(np.abs(self.geometry_matrix[0, row, col] - self.tts_LUT)))  # tts
                    angles.append(np.argmin(np.abs(self.geometry_matrix[1, row, col] - self.tto_LUT)))  # tto
                    angles.append(np.argmin(np.abs(self.geometry_matrix[2, row, col] - self.psi_LUT)))  # psi

                    # find out the number of the LUT to be used - they are sorted in the following order
                    #  0    1    2   ...  5    6   ... ...  31   32   ... n_total   -> for case psin = 6, tton = 5
                    # tts0 tts0 tts0 ... tts0 tts0 ... ... tts0 tts1  ...  ttsn     -> n = self.nangles_LUT[0]
                    # tto0 tto0 tto0 ... tto0 tto1 ... ... tton tto0  ...  tton     -> n = self.nangles_LUT[1]
                    # psi0 psi1 psi2 ... psin psi0 ... ... psin psi0  ...  psin     -> n = self.nangles_LUT[2]
                    self.whichLUT[row, col] = angles[2] * self.nangles_LUT[1] * self.nangles_LUT[0] + \
                                              angles[1] * self.nangles_LUT[0] + \
                                              angles[0]
        else:  # LUT contains only one fixed value
            self.whichLUT[:, :] = 0  # there should only be ONE geo-ensemble for the LUTs and this is #0 then
            self.geometry_matrix[:, :, :] = 911  # a value that is unlikely to be chosen for "no data"
                                                 # In case of geo_mode != 'sort', the matrix is not used anyway

    def add_noise(self, ref_array, noise_type, sigma):
        # noise module to put a noise term on top of PROSAIL spectra

        # Todo: needs testing!!
        # sigma (strength of the noise) is provided as %, so it needs to be converted to relative values
        # and optionally multiplied with the conversion factor to match reflectance value ranges for additive noise
        sigma /= 100
        sigma_converted = sigma * self.conversion_factor

        if noise_type == 1:  # additive noise
            ref_noisy = np.random.normal(loc=0.0, scale=sigma_converted, size=ref_array.shape) + ref_array

        elif noise_type == 2:  # multiplicative noise
            ref_noisy = (1 + np.random.normal(loc=0.0, scale=sigma, size=ref_array.shape)) * ref_array

        elif noise_type == 3:  # inverse multiplicative noise
            ref_noisy = 1 - (1 - ref_array) * (1 + np.random.normal(loc=0.0, scale=sigma))

        else:  # do nothing
            ref_noisy = ref_array

        # replace np.nans and negative values which may occur by adding noise to the data
        ref_noisy[np.isnan(ref_noisy)] = 0
        ref_noisy[ref_noisy < 0] = 0

        return ref_noisy

    @staticmethod
    def _costfun(image_ref, model_ref, ctype):
        # Performing the cost function, i.e. obtaining the "distance" (as in RMSE, MAE or mNSE) between image spectrum
        # and LUT-member -> the function is static (does not depend on the class) and vectorized
        if ctype == 1:  # RMSE
            delta = np.sqrt(np.mean((image_ref - model_ref) ** 2, axis=0))
        elif ctype == 2:  # MAE
            delta = np.sum(np.abs(image_ref - model_ref), axis=0)
        elif ctype == 3:  # mNSE
            delta = 1.0 - ((np.sum(np.abs(image_ref - model_ref), axis=0)) /
                           (np.sum(np.abs(image_ref - (np.mean(image_ref))))))
        else:
            delta = None
            exit("wrong cost function type. Expected 1, 2 or 3; got %i instead" % ctype)

        return delta

    def get_lutmeta(self, file):
        with open(file, 'r') as metafile:
            metacontent = metafile.readlines()
            metacontent = [line.rstrip('\n') for line in metacontent]

        self.LUT_base = os.path.dirname(file) + "/" + metacontent[0].split("=")[1]  # build full path from LUT name
        self.ntotal = int(metacontent[1].split("=")[1])
        self.ns = int(metacontent[2].split("=")[1])
        self.lop = metacontent[3].split("=")[1]  # which leaf optical properties model (ProspectX)?
        self.canopy_arch = metacontent[4].split("=")[1]
        self.geo_mode = metacontent[5].split("=")[1]  # sorted vs. fixed
        self.geo_ensembles = int(metacontent[6].split("=")[1])  # how many geo-ensembles (geometrical constellations)
        self.splits = int(metacontent[7].split("=")[1])  # how many splits per ensemble
        self.max_file_length = int(metacontent[8].split("=")[1])  # how many LUT entries per split?

        temp = metacontent[9].split("=")[1].split(";")
        if "NA" not in temp:
            self.tts_LUT = [float(angle) for angle in temp]
        else:
            self.tts_LUT = []

        temp = metacontent[10].split("=")[1].split(";")
        if "NA" not in temp:
            self.tto_LUT = [float(angle) for angle in temp]
        else:
            self.tto_LUT = []

        temp = metacontent[11].split("=")[1].split(";")
        if "NA" not in temp:
            self.psi_LUT = [float(angle) for angle in temp]
        else:
            self.psi_LUT = []

        self.conversion_factor = int(metacontent[12].split("=")[1])  # the boost of the LUT, e.g. 10000 for EnMAP

        # Attention! The list "whichpara" is NOT a list of the parameters used in the LUT according to the chosen model
        # but it is a FULL list of all possible parameters. e.g. LAIu is always 0 and unused if canopy_arch is not
        # INFORM but it is still there in the LUT (so all LUTs have the same size) -> this only changes if new
        # parameters are added later on!
        self.whichpara = metacontent[13].split("=")[1].split(";")
        self.npara = len(self.whichpara)

        self.nangles_LUT = [len(self.tts_LUT), len(self.tto_LUT), len(self.psi_LUT)]
        if self.nbfits_type == "rel":
            self.nbfits = int(self.ns * (self.nbfits / 100.0))  # convert from % to relative units

    @staticmethod
    def _visualize(image_ref, model_ref):
        # additional method to plot single spectra, may be used by user individually

        # cmap = plt.get_cmap('gnuplot')
        # colors = [cmap(i) for i in np.linspace(0.0, 0.9, len(in_raster))
        # fig = plt.figure(figsize=(10, 5))
        plt.plot(image_ref, color='b')
        plt.show()
        plt.plot(model_ref, color='r')
        plt.show()

    def run_inversion(self, prg_widget=None, qgis_app=None):
        # find out, which "whichLUT" are actually found in the geo_image
        self.whichLUT_unique = np.unique(self.whichLUT)
        whichLUT_coords = list()

        # Working with masks to find out, which pixels need to be inverted. First set the mask to shape and all == True
        all_true = np.full(shape=(self.nrows, self.ncols), fill_value=True)

        # Find out coordinates for which ALL constraints hold True in each "whichLUT"
        for iwhichLUT in self.whichLUT_unique:
            whichLUT_coords.append(np.where((self.whichLUT[:, :] == iwhichLUT) &  # 1: where to find current ensemble
                                            # 2: not masked
                                            (self.mask[0, :, :] > 0 if self.mask is not None else all_true) &
                                            (~np.all(self.image == self.nodat[0], axis=0))))  # 3: not NoDatVal
        pix_current = 0
        # How many pixels are to be inverted at all?
        npixel_valid = sum([len(whichLUT_coords[i][0]) for i in range(len(self.whichLUT_unique))])

        self.out_matrix = np.empty(shape=(self.npara, self.nrows, self.ncols))  # create empty array for outputs

        # Iterate over all LUT ensembles (the coordinates are known from loop above)
        for i_ilut, ilut in enumerate(self.whichLUT_unique):
            if whichLUT_coords[i_ilut][0].size == 0:
                continue  # after masking, not all 'iluts' are present in the image_copy
            # make a list of all files that make up one LUT from splits
            load_objects = [np.load(self.LUT_base + "_" + str(ilut) + "_" + str(split) + ".npy")
                            for split in range(self.splits)]
            lut = np.hstack(load_objects)  # load all splits of the current geo_ensembles into "lut"

            lut_params = lut[:self.npara, :]  # extract parameters - they are at the beginning rows of lut
            lut = np.delete(lut, self.exclude_bands_model, axis=0)  # delete exclude_bands_model - members
            lut = self.add_noise(ref_array=lut, noise_type=self.noisetype, sigma=self.noiselevel)  # add noise

            samples_size = len(whichLUT_coords[i_ilut][0])  # how many pixels in the current iLUT (whichLUT member)
            result = np.zeros(shape=(self.npara, samples_size))

            # Iterate over each pixel sample (whichLUT)
            for isample in range(samples_size):
                # Get reflectance data of the current sample (all pixels at once)
                mydata = self.image[:, whichLUT_coords[i_ilut][0][isample], whichLUT_coords[i_ilut][1][isample]]

                # calculate distances between sample and all LUT-members of iLUT
                estimates = self._costfun(image_ref=mydata[:, np.newaxis], model_ref=lut, ctype=self.ctype)
                pix_current += 1
                if isample % 1000 == 0:  # update the progress bar every 1000 pixels
                    if prg_widget:
                        pix_limit = pix_current + 999
                        if pix_limit > npixel_valid:
                            pix_limit = npixel_valid
                        prg_widget.gui.lblCaption_r.setText('Inverting pixels {:d}-{:d} of {:d}'
                                                            .format(pix_current, pix_limit, npixel_valid))
                        prg_widget.gui.prgBar.setValue(pix_current * 100 // npixel_valid)
                        qgis_app.processEvents()
                    else:
                        print("LUT_unique #{:d} of {:d}: Checking sample {:d} of {:d}"
                              .format(i_ilut, len(self.whichLUT_unique), isample, samples_size))

                # nbest_subset is a subset of LUT for the n best performing entries
                nbest_subset = np.argpartition(estimates, self.nbfits)[0:self.nbfits]
                # sort in order of distance: closest match is nbest_subset[0]
                nbest_subset = nbest_subset[np.argsort(estimates[nbest_subset])]

                # Obtain the final result for this sample: The median of the subset
                result[:, isample] = np.median(lut_params[:, nbest_subset], axis=1)

                # Visualize: turn this on and specify WHEN to visualize if necessary
                # self._visualize(image_ref == mydata, model_ref=nbest_subset[0])

            # Place all results for this whichLUT run in the out_matrix
            self.out_matrix[:, whichLUT_coords[i_ilut][0], whichLUT_coords[i_ilut][1]] = result

    def write_image(self):
        # write output to file(s), use the same grid as the input image
        if self.out_mode == "single":
            output = Raster.fromArray(array=self.out_matrix, filename=self.image_out, grid=self.grid)
            output.dataset().setMetadataItem('data ignore value', self.nodat[2], 'ENVI')
            for i, band in enumerate(output.dataset().bands()):
                band.setDescription(self.whichpara[i])
                band.setNoDataValue(self.nodat[2])

        elif self.out_mode == "individual":
            for i, para_key in enumerate(self.whichpara):
                output = Raster.fromArray(array=self.out_matrix[i, :, :][np.newaxis, :, :], filename=os.path.splitext(
                    self.image_out)[0] + "_" + para_key + os.path.splitext(self.image_out)[1])
                output.dataset().setMetadataItem('data ignore value', self.nodat[2], 'ENVI')
                for band in output.dataset().bands():
                    band.setDescription(para_key)
                    band.setNoDataValue(self.nodat[2])
