# -*- coding: utf-8 -*-
# This script is the successor of AVI Agricultural Vegetation Index
# New: the user can choose how to select wavelengths (nearest neighbor, linear, IDW, Spline)

import numpy as np
from enmapbox.coreapps._classic.hubflow.core import *


# The class VIT (Vegetation Index Toolbox) handles all the preparation and calculation
class VIT:
    def __init__(self, interpolation_type, nodat, division_factor, idw_exp=None):

        self.nodat = nodat  # set no data value ([0]: in, []1: out)
        self.interpolation_type = interpolation_type  # Interpolation type: 1: NN, 2: linear, 3: IDW, 4: Spline
        self.idw_exp = idw_exp  # In case of interpolation_type = IDW, set power of IDW
        self.division_factor = division_factor

    @staticmethod
    def _norm_diff1(a, b):  # Normalized Difference Index: ARRAYS as input
        return (a - b) / (a + b)

    def norm_diff2(self, a, b):  # Normalized Difference Index: BAND NUMBER as input
        return (self.ImageIn_matrix[:, :, a] -
                self.ImageIn_matrix[:, :, b]) / (self.ImageIn_matrix[:, :, a] +
                                                 self.ImageIn_matrix[:, :, b])

    def division(self, a, b):  # Simple Division: BAND NUMBER as input
        return self.ImageIn_matrix[:, :, a] / self.ImageIn_matrix[:, :, b]

    @staticmethod
    def _detect_band_anomaly(bands):
        # this static method scans the list of bands and checks for the typical EnMAP-band anomaly of overlapping
        # wavelengts of VNIR and SWIR and returns the SWIR-bands to be removed
        wl_diff = np.diff(bands)  # find difference between bands[i] and bands[i+1]
        last_vnir = int(np.argmax(wl_diff < 0))  # find first occurrance of negative difference (= tipping point)

        if not last_vnir:
            exclude_bands = list()  # return empty list if no anomaly was found
        else:
            # Exclude all bands with index higher than last_vnir and wavelength lower than last_vnir
            exclude_bands = [i for i in range(last_vnir + 1, len(bands)) if bands[i] < bands[last_vnir]]

        return exclude_bands

    def toggle_indices(self, StructIndices, ChlIndices, CarIndices, WatIndices, DmIndices, FlIndices):
        # Prepare which indices should be used: Boolean lists for index groups
        self.StructIndices = StructIndices
        self.ChlIndices = ChlIndices
        self.CarIndices = CarIndices
        self.WatIndices = WatIndices
        self.DmIndices = DmIndices
        self.FlIndices = FlIndices

        # How many & which indices are calculated? Concatenate for easier access
        concat_indices = StructIndices + ChlIndices + CarIndices + WatIndices + DmIndices + FlIndices
        self.n_indices = sum(concat_indices[i] for i in range(len(concat_indices)) if concat_indices[i] > 0)

        all_labels = ["hNDVI_Opp", "NDVI_Apr", "NDVI_Dat", "NDVI_Hab", "NDVI_Zar", "MCARI1", "MCARI2", "MSAVI", "MTVI1",
                      "MTVI2",
                      "OSAVI", "RDVI", "SPVI", "CSI1", "CSI2", "G", "GM1", "GM2", "gNDVI", "MCARI", "NPQI", "PRI",
                      "REIP1",
                      "REP", "SRchl", "SR705", "TCARI", "TVI", "VOG1", "VOG2", "ZTM", "SRa", "SRb", "SRb2",
                      "SRtot",
                      "PSSRa", "PSSRb", "LCI", "MLO", "ARI", "CRI", "CRI2", "PSSRc", "SIPI", "DSWI", "DWSI5",
                      "LMVI1", "LMVI2",
                      "MSI", "NDWI", "PWI", "SRWI", "SMIRVI", "CAI", "NDLI", "NDNI", "BGI", "BRI", "RGI", "SRPI",
                      "NPCI", "NDI", "CUR", "LIC1", "LIC2", "LIC3"]

        # sort out only the labels for the indices which should be calculated
        self.labels = [all_labels[i] for i in range(len(all_labels)) if concat_indices[i] == 1]

    def prepare_indices(self):
        # List of wavelengths [nm] used for any of the indices. Append for new index!
        wl_list = np.array([415, 420, 430, 435, 440, 445, 450, 500, 510, 528, 531, 547, 550, 554, 567, 645, 650, 665,
                            668, 670, 672, 675, 677, 680, 682, 683, 690, 695, 700, 701, 705, 708, 710, 715, 720, 724,
                            726, 734, 740, 745, 747, 750, 760, 774, 780, 800, 802, 820, 827, 831, 850, 858, 860, 900,
                            970, 983, 1094, 1205, 1240, 1460, 1510, 1600, 1657, 1660, 1680, 2015, 2090, 2106, 2114,
                            2195, 2208, 2210])

        self.loc_b(wl_array=wl_list)  # Assign required wavelengths to sensor wavelengths

    def read_image(self, image):
        # Read spectral image
        dataset = openRasterDataset(image)

        try:
            # Get grid from dataset
            self.grid = dataset.grid()
        except:
            raise Warning("No CRS provided in Input Image")

        metadict = dataset.metadataDict()  # read the metadata of the header

        self.nrows = int(metadict['ENVI']['lines'])
        self.ncols = int(metadict['ENVI']['samples'])
        nbands = int(metadict['ENVI']['bands'])

        try:
            wave_dict = metadict['ENVI']['wavelength']
        except:
            raise ValueError('No wavelengths provided in ENVI header file')

        if metadict['ENVI']['wavelength'] is None:
            raise ValueError('No wavelengths provided in ENVI header file')
        elif metadict['ENVI']['wavelength units'].lower() in \
                ['nanometers', 'nm', 'nanometer']:
            wave_convert = 1  # conversion factor to nm
        elif metadict['ENVI']['wavelength units'].lower() in \
                ['micrometers', 'µm', 'micrometer']:
            wave_convert = 1000  # conversion factor to nm
        else:
            raise ValueError(
                "Wavelength units must be nanometers or micrometers. Got '%s' instead" %
                metadict['ENVI']['wavelength units'])

        in_matrix = dataset.readAsArray()  # read the spectral information into in_matrix

        # In the GUI, a division factor may be set to convert higher reflectance scales down to [0...1], which
        # is mandatory for index calculation!
        if self.division_factor != 1.0:
            in_matrix = in_matrix / self.division_factor

        # Obtain wavelengths of the input image
        self.wl = [float(item) * wave_convert for item in wave_dict]
        self.wl = [int(i) for i in self.wl]

        # Detect EnMAP band anomaly
        exclude = self._detect_band_anomaly(bands=self.wl)
        self.wl = np.asarray([self.wl[i] for i in range(len(self.wl)) if i not in exclude])
        self.n_wl = len(self.wl)

        band_range = [i for i in range(nbands) if i not in exclude]  # list of valid bands of the original (!) sensor wl
        self.dict_band = dict(zip(self.wl, band_range))  # maps wavelengths to (valid) sensor bands

        in_matrix = np.swapaxes(in_matrix, 0, 1)  # hubflow has a different order than the script; it is easier to swap
        in_matrix = np.swapaxes(in_matrix, 1, 2)
        self.mask = np.all(in_matrix == int(self.nodat[0]), axis=2)  # mask all pixels full of no data
        self.ImageIn_matrix = in_matrix

        return in_matrix

    def loc_b(self, wl_array):
        # creates a dict that zips each index-wavelength to a sensor band
        # wl_target are the available wavelengths for the ones needed for the indices
        band_out = list()
        for wl_in in wl_array:
            if self.interpolation_type == 1:  # nearest neighbor
                distances = np.abs(wl_in - self.wl)  # calculate the distances between index-wl and sensor-wls
                wl_target = self.dict_band[self.wl[np.argmin(distances)]]  # find the nearest one in sensor_wls

            elif self.interpolation_type == 2:  # linear
                if wl_in in self.wl:  # if wl_in is actually available, do not interpolate
                    wl_target = self.dict_band[wl_in]
                else:
                    distances = wl_in - self.wl
                    # find left and right index (nearest smaller and nearest larger wavelength)
                    # set all values >/< 0 to inf/-inf to perform argmin/argmax (smallest positive, highest negative)
                    ind_left = np.where(distances > 0, distances, np.inf).argmin()
                    ind_right = np.where(distances < 0, distances, -np.inf).argmax()

                    # if the input wavelength does not have a left AND right neighbor,
                    # perform Nearest Neighbor int instead
                    if (ind_left == ind_right == 0) or (ind_left == ind_right == self.n_wl):
                        distances = np.abs(wl_in - self.wl)
                        wl_target = self.dict_band[self.wl[np.argmin(distances)]]
                    else:
                        band_left = self.dict_band[self.wl[ind_left]]  # find correct band number left
                        band_right = self.dict_band[self.wl[ind_right]]  # find correct band number right

                        # Linear interpolation of the band
                        wl_target = (band_right - band_left) * (wl_in - self.wl[ind_left]) / (
                            self.wl[ind_right] - self.wl[ind_left]) + band_left

            elif self.interpolation_type == 3:  # IDW
                if wl_in in self.wl:  # if wl_in is actually available, do not interpolate
                    wl_target = self.dict_band[wl_in]
                else:
                    distances = wl_in - self.wl
                    dist_left = np.min(np.where(distances > 0, distances, np.inf))
                    dist_right = np.max(np.where(distances < 0, distances, -np.inf))
                    ind_left = np.where(distances > 0, distances, np.inf).argmin()
                    ind_right = np.where(distances < 0, distances, -np.inf).argmax()

                    # if the input wavelength does not have a left AND right neighbor,
                    # perform Nearest Neighbor int instead
                    if (ind_left == ind_right == 0) or (ind_left == ind_right == self.n_wl):
                        distances = np.abs(wl_in - self.wl)
                        wl_target = self.dict_band[self.wl[np.argmin(distances)]]
                    else:
                        band_left = self.dict_band[self.wl[ind_left]]
                        band_right = self.dict_band[self.wl[ind_right]]

                        # perform inverse-distance weighting
                        weights = [0] * 2
                        weights[0] = 1 / (dist_left ** self.idw_exp)
                        weights[1] = 1 / (np.abs(dist_right) ** self.idw_exp)
                        wl_target = (band_left * weights[0] + band_right * weights[1]) / np.sum(weights)
            
            else:
                return

            # band_out contains the sensor-available wavelengths that can be used for calculation of the indices
            band_out.append(wl_target)
            band_out = [int(band_out[i]) for i in range(len(band_out))]

        self.dict_senswl = dict(zip(wl_array, band_out))  # maps index wavelengths with sensor bands

    def prgbar_process(self, index_no):
        # Method to control the progress bar
        if self.prg:
            if self.prg.gui.lblCancel.text() == "-1":  # Cancel has been hit shortly before
                self.prg.gui.lblCancel.setText("")
                self.prg.gui.cmdCancel.setDisabled(False)
                raise ValueError("Calculation of Indices canceled")
            self.prg.gui.prgBar.setValue(index_no * 100 // self.n_indices)  # progress value is index-orientated
            self.qgis_app.processEvents() 

    def calculate_VIT(self, prg_widget=None, qgis_app=None):
        # Core algorithm to calculate the selected indices
        self.prg = prg_widget
        self.qgis_app = qgis_app

        # override numpy-settings: math errors will be ignored (nodata will remain in matrix)
        old_settings = np.seterr(all='ignore') 

        temp_val = np.zeros(shape=(self.nrows, self.ncols, 11), dtype=np.float16)  # initialize temp values dumper
        index_no = 0  # intialize index_counter
        index_out_matrix = np.full(shape=(self.nrows, self.ncols, self.n_indices), fill_value=self.nodat[1], dtype=float)

        # Browse through all sections (categories) and if one single index from the category is selected,
        # browse through all indices of the section and choose the appropriate index type
        # Basic math calculations are defined in functions to handle nodata and ZeroDivisionErrors
        # Attention: Some methods take wavelengths, others take reflectances!
        
        if 1 in self.StructIndices:
            if self.StructIndices[0] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[827], self.dict_senswl[668])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[1] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[900], self.dict_senswl[680])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[2] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[800], self.dict_senswl[680])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[3] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[800], self.dict_senswl[670])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[4] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[774], self.dict_senswl[677])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[5] == 1:
                temp_val[:, :, 0] = 2.5 * (self.ImageIn_matrix[:, :, self.dict_senswl[800]] - 
                                           self.ImageIn_matrix[:, :, self.dict_senswl[670]])
                temp_val[:, :, 1] = 1.3 * (self.ImageIn_matrix[:, :, self.dict_senswl[800]] - 
                                           self.ImageIn_matrix[:, :, self.dict_senswl[550]])
                index_out_matrix[:, :, index_no] = 1.2 * (temp_val[:, :, 0] - temp_val[:, :, 1])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[6] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[550]]
                temp_val[:, :, 3] = np.sqrt(self.ImageIn_matrix[:, :, self.dict_senswl[680]])
                temp_val[:, :, 4] = 1.5 * (2.5 * (temp_val[:, :, 0] - temp_val[:, :, 1]) - 
                                           1.3 * (temp_val[:, :, 0] - temp_val[:, :, 2]))
                temp_val[:, :, 5] = (2 * temp_val[:, :, 0] + 1) ** 2
                temp_val[:, :, 6] = 6 * temp_val[:, :, 0] - 5 * temp_val[:, :, 3]
                temp_val[:, :, 7] = np.sqrt(temp_val[:, :, 5] - temp_val[:, :, 6] - 0.5)
                index_out_matrix[:, :, index_no] = temp_val[:, :, 4] / temp_val[:, :, 7]
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[7] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = 2 * temp_val[:, :, 0] + 1
                temp_val[:, :, 3] = temp_val[:, :, 2] ** 2
                temp_val[:, :, 4] = 8 * (temp_val[:, :, 0] - temp_val[:, :, 1])
                temp_val[:, :, 5] = np.sqrt(temp_val[:, :, 3] - temp_val[:, :, 4])
                index_out_matrix[:, :, index_no] = 0.5 * (temp_val[:, :, 2] - temp_val[:, :, 5])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[8] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[550]]
                temp_val[:, :, 3] = 1.2 * (temp_val[:, :, 0] - temp_val[:, :, 2])
                temp_val[:, :, 4] = 2.5 * (temp_val[:, :, 1] - temp_val[:, :, 2])
                index_out_matrix[:, :, index_no] = 1.2 * (temp_val[:, :, 3] - temp_val[:, :, 4])
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[9] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[550]]
                temp_val[:, :, 3] = 1.2 * (temp_val[:, :, 0] - temp_val[:, :, 2])
                temp_val[:, :, 4] = 2.5 * (temp_val[:, :, 1] - temp_val[:, :, 2])
                temp_val[:, :, 5] = 1.5 * (temp_val[:, :, 3] - temp_val[:, :, 4])
                temp_val[:, :, 6] = (2 * temp_val[:, :, 0] + 1) ** 2
                temp_val[:, :, 7] = 6 * temp_val[:, :, 0]
                temp_val[:, :, 8] = 5 * np.sqrt(temp_val[:, :, 1])
                temp_val[:, :, 9] = temp_val[:, :, 7] - temp_val[:, :, 8]
                temp_val[:, :, 10] = np.sqrt(temp_val[:, :, 6] - temp_val[:, :, 9] - 0.5)
                index_out_matrix[:, :, index_no] = temp_val[:, :, 5] / temp_val[:, :, 10]
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[10] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = 1.16 * (temp_val[:, :, 0] - temp_val[:, :, 1])
                temp_val[:, :, 3] = temp_val[:, :, 0] + temp_val[:, :, 1] + 0.16
                index_out_matrix[:, :, index_no] = temp_val[:, :, 2] / temp_val[:, :, 3]
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[11] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = temp_val[:, :, 0] - temp_val[:, :, 1]
                temp_val[:, :, 3] = np.sqrt(temp_val[:, :, 0] + temp_val[:, :, 1])
                index_out_matrix[:, :, index_no] = temp_val[:, :, 2] / temp_val[:, :, 3]
                index_no += 1
                self.prgbar_process(index_no)
            if self.StructIndices[12] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[531]]
                temp_val[:, :, 3] = 3.7 * (temp_val[:, :, 0] - temp_val[:, :, 1])
                temp_val[:, :, 4] = 1.2 * (temp_val[:, :, 2] - temp_val[:, :, 1])
                index_out_matrix[:, :, index_no] = 0.4 * (temp_val[:, :, 3] - temp_val[:, :, 4])
                index_no += 1
                self.prgbar_process(index_no)

        if 1 in self.ChlIndices:
            if self.ChlIndices[0] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[695], self.dict_senswl[420])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[1] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[695], self.dict_senswl[760])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[2] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[554], self.dict_senswl[677])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[3] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[750], self.dict_senswl[550])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[4] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[750], self.dict_senswl[700])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[5] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[750], self.dict_senswl[550])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[6] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[700]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[550]]
                index_out_matrix[:, :, index_no] = ((temp_val[:, :, 0] - temp_val[:, :, 1]) - 0.2 *
                                                    (temp_val[:, :, 0] - temp_val[:, :, 2])) * \
                                                   (temp_val[:, :, 0] / temp_val[:, :, 1])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[7] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[415], self.dict_senswl[435])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[8] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[528], self.dict_senswl[567])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[9] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[780]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[740]]
                temp_val[:, :, 3] = self.ImageIn_matrix[:, :, self.dict_senswl[701]]
                index_out_matrix[:, :, index_no] = 700 + (740 / 700) * ((temp_val[:, :, 0] / temp_val[:, :, 1]) -
                                                                        temp_val[:, :, 0]) / (temp_val[:, :, 2] +
                                                                                              temp_val[:, :, 3])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[10] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[780]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[740]]
                temp_val[:, :, 3] = self.ImageIn_matrix[:, :, self.dict_senswl[700]]
                index_out_matrix[:, :, index_no] = 700 + 40 * (((temp_val[:, :, 1] + temp_val[:, :, 0]) / 2 -
                                                                temp_val[:, :, 3]) / (temp_val[:, :, 2] +
                                                                                      temp_val[:, :, 3]))
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[11] == 1:
                index_out_matrix[:, :, index_no] = self.ImageIn_matrix[:, :, self.dict_senswl[672]] / \
                                                (self.ImageIn_matrix[:, :, self.dict_senswl[550]] *
                                                 self.ImageIn_matrix[:, :, self.dict_senswl[708]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[12] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[750], self.dict_senswl[705])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[13] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[700]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[550]]
                index_out_matrix[:, :, index_no] = 3 * ((temp_val[:, :, 0] - temp_val[:, :, 1]) -
                                                        0.2 * (temp_val[:, :, 0] - temp_val[:, :, 2])) * \
                                                       (temp_val[:, :, 0] / temp_val[:, :, 1])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[14] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[750]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[670]]
                temp_val[:, :, 2] = self.ImageIn_matrix[:, :, self.dict_senswl[550]]
                index_out_matrix[:, :, index_no] = 0.5 * (120 * (temp_val[:, :, 0] - temp_val[:, :, 2]) -
                                                          200 * (temp_val[:, :, 1] - temp_val[:, :, 2]))
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[15] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[740], self.dict_senswl[720])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[16] == 1:
                index_out_matrix[:, :, index_no] = (self.dict_senswl[734] - self.dict_senswl[747]) / \
                                                   (self.dict_senswl[715] + self.dict_senswl[726])

                index_no += 1
                self.prgbar_process(index_no)
                # former ChlIndices16 is now skipped!

            if self.ChlIndices[17] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[750], self.dict_senswl[710])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[18] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[675], self.dict_senswl[700])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[19] == 1:
                index_out_matrix[:, :, index_no] = self.ImageIn_matrix[:, :, self.dict_senswl[672]] / \
                                                (self.ImageIn_matrix[:, :, self.dict_senswl[650]] *
                                                 self.ImageIn_matrix[:, :, self.dict_senswl[700]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[20] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[672], self.dict_senswl[708])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[21] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[760], self.dict_senswl[550])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[22] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[800], self.dict_senswl[675])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[23] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[800], self.dict_senswl[650])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[24] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[745], self.dict_senswl[724])
                index_no += 1
                self.prgbar_process(index_no)
            if self.ChlIndices[25] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[531], self.dict_senswl[645])
                index_no += 1
                self.prgbar_process(index_no)

        if 1 in self.CarIndices:
            if self.CarIndices[0] == 1:
                index_out_matrix[:, :, index_no] = (1 / self.ImageIn_matrix[:, :, self.dict_senswl[550]]) \
                                                - (1 / self.ImageIn_matrix[:, :, self.dict_senswl[700]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.CarIndices[1] == 1:
                index_out_matrix[:, :, index_no] = (1 / self.ImageIn_matrix[:, :, self.dict_senswl[510]]) \
                                                  - (1 / self.ImageIn_matrix[:, :, self.dict_senswl[550]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.CarIndices[2] == 1:
                index_out_matrix[:, :, index_no] = (1 / self.ImageIn_matrix[:, :, self.dict_senswl[510]]) \
                                                  - (1 / self.ImageIn_matrix[:, :, self.dict_senswl[700]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.CarIndices[3] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[800], self.dict_senswl[500])
                index_no += 1
                self.prgbar_process(index_no)
            if self.CarIndices[4] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[800]]
                index_out_matrix[:, :, index_no] = (self.ImageIn_matrix[:, :, self.dict_senswl[445]] -
                                                    temp_val[:, :, 0]) / \
                                                   (self.ImageIn_matrix[:, :, self.dict_senswl[680]] -
                                                    temp_val[:, :, 0])
                index_no += 1
                self.prgbar_process(index_no)
        if 1 in self.WatIndices:
            if self.WatIndices[0] == 1:
                index_out_matrix[:, :, index_no] = (self.ImageIn_matrix[:, :, self.dict_senswl[802]] -
                                                    self.ImageIn_matrix[:, :, self.dict_senswl[547]]) / \
                                                   (self.ImageIn_matrix[:, :, self.dict_senswl[1657]] +
                                                    self.ImageIn_matrix[:, :, self.dict_senswl[682]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[1] == 1:
                index_out_matrix[:, :, index_no] = (self.ImageIn_matrix[:, :, self.dict_senswl[800]] +
                                                    self.ImageIn_matrix[:, :, self.dict_senswl[550]]) / \
                                                   (self.ImageIn_matrix[:, :, self.dict_senswl[1660]] +
                                                    self.ImageIn_matrix[:, :, self.dict_senswl[680]])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[2] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[1094], self.dict_senswl[983])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[3] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[1094], self.dict_senswl[1205])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[4] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[1600], self.dict_senswl[820])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[5] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[860], self.dict_senswl[1240])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[6] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[970], self.dict_senswl[900])
                index_no += 1
                self.prgbar_process(index_no)
            if self.WatIndices[7] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[858], self.dict_senswl[1240])
                index_no += 1
                self.prgbar_process(index_no)

        if 1 in self.DmIndices:
            if self.DmIndices[0] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[2090]]
                index_out_matrix[:, :, index_no] = 37.27 * (self.ImageIn_matrix[:, :, self.dict_senswl[2210]] +
                                                            temp_val[:, :, 0]) + 26.27 * \
                                                           (self.ImageIn_matrix[:, :, self.dict_senswl[2208]] -
                                                            temp_val[:, :, 0]) - 0.57
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[1] == 1:
                index_out_matrix[:, :, index_no] = 0.5 * (
                    self.ImageIn_matrix[:, :, self.dict_senswl[2015]] +
                    self.ImageIn_matrix[:, :, self.dict_senswl[2195]]) - \
                                                self.ImageIn_matrix[:, :, self.dict_senswl[2106]]
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[2] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[1094]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[1205]]
                index_out_matrix[:, :, index_no] = self._norm_diff1((1 / np.log10(temp_val[:, :, 0])),
                                                                    (1 / np.log10(temp_val[:, :, 1])))
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[3] == 1:
                temp_val[:, :, 0] = self.ImageIn_matrix[:, :, self.dict_senswl[1510]]
                temp_val[:, :, 1] = self.ImageIn_matrix[:, :, self.dict_senswl[1680]]
                index_out_matrix[:, :, index_no] = self._norm_diff1((1 / np.log10(temp_val[:, :, 0])),
                                                                    (1 / np.log10(temp_val[:, :, 1])))
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[4] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[450], self.dict_senswl[550])
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[5] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[450], self.dict_senswl[690])
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[6] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[690], self.dict_senswl[550])
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[7] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[430], self.dict_senswl[680])
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[8] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[680], self.dict_senswl[430])
                index_no += 1
                self.prgbar_process(index_no)
            if self.DmIndices[9] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[1460], self.dict_senswl[2114])
                index_no += 1
                self.prgbar_process(index_no)

        if 1 in self.FlIndices:
            if self.FlIndices[0] == 1:
                index_out_matrix[:, :, index_no] = (self.ImageIn_matrix[:, :, self.dict_senswl[675]] *
                                                    self.ImageIn_matrix[:, :, self.dict_senswl[550]]) / \
                                                   (self.ImageIn_matrix[:, :, self.dict_senswl[683]] ** 2)
                index_no += 1
                self.prgbar_process(index_no)
            if self.FlIndices[1] == 1:
                index_out_matrix[:, :, index_no] = self.norm_diff2(self.dict_senswl[800], self.dict_senswl[680])
                index_no += 1
                self.prgbar_process(index_no)
            if self.FlIndices[2] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[440], self.dict_senswl[690])
                index_no += 1
                self.prgbar_process(index_no)
            if self.FlIndices[3] == 1:
                index_out_matrix[:, :, index_no] = self.division(self.dict_senswl[440], self.dict_senswl[740])
                index_no += 1
                self.prgbar_process(index_no)

        np.seterr(**old_settings)  # restore old numpy settings

        # change nan and inf into nodat
        index_out_matrix[np.logical_or(np.isnan(index_out_matrix), np.isinf(index_out_matrix))] = self.nodat[1]

        self.mask = np.dstack([self.mask] * self.n_indices)  # expand mask to match the shape of the output
        index_out_matrix[self.mask] = self.nodat[1]  # change masked no data values of input to nodat

        # due to hubflow.core write image handling axis sequence had to be changed to [bands, rows, cols]
        # -> Transpose matrix back to normal
        index_out_matrix = np.transpose(index_out_matrix, [2, 0, 1])

        return index_out_matrix

    def write_out(self, index_out_matrix, out_dir, out_filename, out_single):
        # Write index-results to file (BSQ)
        if out_single == 1:  # Output to single file
            output = Raster.fromArray(array=index_out_matrix, filename=out_dir + out_filename,
                                      grid=self.grid)
            output.dataset().setMetadataItem('data ignore value', self.nodat[1], 'ENVI')
            for i, band in enumerate(output.dataset().bands()):
                band.setDescription(self.labels[i])
                band.setNoDataValue(self.nodat[1])

        else:  # Output to individual files
            for i in range(self.n_indices):
                # for each index, create an empty 3D-array
                out_array = np.zeros((1, index_out_matrix.shape[1], index_out_matrix.shape[2]))
                out_array[0, :, :] = index_out_matrix[i, :, :]  # fill it with the index results
                output = Raster.fromArray(array=out_array, filename=out_dir + out_filename + '_' +
                                                                    self.labels[i], grid=self.grid)
                output.dataset().setMetadataItem('data ignore value', self.nodat[1], 'ENVI')
                for band in output.dataset().bands():
                    band.setDescription(self.labels[i])
                    band.setNoDataValue(self.nodat[1])
