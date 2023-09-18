# -*- coding: utf-8 -*-
"""
***************************************************************************
    call_model.py
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
    call_model.py routine handles the execution of PROSAIL in different forms
    This version is vectorized, i.e. the idea is to pass several parameter inputs at once to obtain an array of results
    But it is also used for single outputs

"""

import os
import numpy as np
from scipy.stats import truncnorm
import lmuvegetationapps.Resources.PROSAIL.SAIL as SAIL_v
import lmuvegetationapps.Resources.PROSAIL.INFORM as INFORM_v
import lmuvegetationapps.Resources.PROSAIL.prospect as prospect_v
from lmuvegetationapps.Resources.PROSAIL.dataSpec import lambd
from lmuvegetationapps.Resources.Spec2Sensor.Spec2Sensor_core import Spec2Sensor
import warnings
import time

warnings.filterwarnings('ignore')  # do not show warnings (set to 'all' if you want to see warnings, too)


# This class creates instances of the actual models and is fed with parameter inputs
class CallModel:

    def __init__(self, soil, paras):
        # paras is a dictionary of all input parameters; this allows flexible adding/removing for new models
        self.par = paras
        self.ninputs = self.par['cab'].shape[0]  # cab is always part of self.par, so it is used to obtain ninputs
        self.soil = soil

    def call_prospect4(self):
        prospect_instance = prospect_v.Prospect()
        self.prospect = prospect_instance.prospect_4(self.par["N"], self.par["cab"], self.par["cw"], self.par["cm"])

        return self.prospect

    def call_prospect5(self):
        prospect_instance = prospect_v.Prospect()
        self.prospect = prospect_instance.prospect_5(self.par["N"], self.par["cab"], self.par["car"], self.par["cw"],
                                                     self.par["cm"])

        return self.prospect

    def call_prospect5b(self):
        prospect_instance = prospect_v.Prospect()
        self.prospect = prospect_instance.prospect_5B(self.par["N"], self.par["cab"], self.par["car"],
                                                      self.par["cbrown"], self.par["cw"], self.par["cm"])

        return self.prospect

    def call_prospectD(self):
        prospect_instance = prospect_v.Prospect()
        self.prospect = prospect_instance.prospect_D(self.par["N"], self.par["cab"], self.par["car"], self.par["anth"],
                                                     self.par["cbrown"], self.par["cw"], self.par["cm"])
        return self.prospect

    def call_prospectPro(self):
        prospect_instance = prospect_v.Prospect()
        self.prospect = prospect_instance.prospect_Pro(self.par["N"], self.par["cab"], self.par["car"],
                                                      self.par["anth"],
                                                      self.par["cp"], self.par["cbc"], self.par["cbrown"],
                                                      self.par["cw"])
        return self.prospect

    ## All returns from "self.prospects" are in the following shape:
    # dim one: number of runs for vectorized version
    # dim two: number of wavebands (2101)
    # dim three: [0] wavelengths;[1] reflectances; [2] transmittances

    def call_4sail(self):
        try:
            self.prospect.any()  # 4sail can only be called when PROSAIL has been run first
        except ValueError:
            raise ValueError("A leaf optical properties model needs to be run first!")

        sail_instance = SAIL_v.Sail(np.deg2rad(self.par["tts"]), np.deg2rad(self.par["tto"]),
                                    np.deg2rad(self.par["psi"]))   # Create Instance of SAIL and initialize angles

        self.sail = sail_instance.pro4sail(self.prospect[:, :, 1], self.prospect[:, :, 2], self.par["LIDF"],
                                           self.par["typeLIDF"], self.par["LAI"], self.par["hspot"], self.par["psoil"],
                                           self.soil)  # call 4SAIL from the SAIL instance

        # # SAIL with "skyl" as additional parameter -> temporarily disabled
        # self.sail = sail_instance.Pro4sail(self.prospect[:, :, 1], self.prospect[:, :, 2], self.par["LIDF"],
        #                                    self.par["typeLIDF"], self.par["LAI"], self.par["hspot"], self.par["psoil"],
        #                                    self.soil, self.par["skyl"])  # call 4SAIL from the SAIL instance

        return self.sail

    def call_inform(self):
        try:
            self.prospect.any()
        except ValueError:
            raise ValueError("A leaf optical properties model needs to be run first!")
        sail_instance = SAIL_v.Sail(np.deg2rad(self.par["tts"]), np.deg2rad(self.par["tto"]),
                                    np.deg2rad(self.par["psi"]))  # Create Instance of SAIL and initialize angles

        # Step 1: call Pro4sail to calculate understory reflectance
        self.sail_understory_refl = sail_instance.pro4sail(self.prospect[:, :, 1], self.prospect[:, :, 2], self.par["LIDF"],
                                                           self.par["typeLIDF"], self.par["LAIu"], self.par["hspot"], self.par["psoil"],
                                                           self.soil)

        # Step 2: call Pro4sail with understory as soil to calculate infinite crown reflectance
        inform_temp_LAI = np.asarray([15]*self.ninputs).T  # vectorized: intialize extreme LAI ninputs times
        inform_temp_hspot = np.asarray([0]*self.ninputs).T  # vectorized: initialize hspot = 0 ninputs times
        self.sail_inf_refl = sail_instance.pro4sail(self.prospect[:, :, 1], self.prospect[:, :, 2], self.par["LIDF"],
                                                    self.par["typeLIDF"], inform_temp_LAI, self.par["hspot"],
                                                    psoil=None, soil=None, understory=self.sail_understory_refl)

        self.sail_tts_trans = sail_instance.pro4sail(self.prospect[:, :, 1], self.prospect[:, :, 2], self.par["LIDF"],
                                                     self.par["typeLIDF"], self.par["LAI"], inform_temp_hspot,
                                                     psoil=None, soil=None, understory=self.sail_understory_refl,
                                                     inform_trans='tts')

        self.sail_tto_trans = sail_instance.pro4sail(self.prospect[:, :, 1], self.prospect[:, :, 2], self.par["LIDF"],
                                                     self.par["typeLIDF"], self.par["LAI"], inform_temp_hspot,
                                                     psoil=None, soil=None, understory=self.sail_understory_refl,
                                                     inform_trans='tto')

        inform_instance = INFORM_v.INFORM(sail_instance.costts, sail_instance.costto, sail_instance.cospsi)
        inform = inform_instance.inform(self.par["cd"], self.par["sd"], self.par["h"], self.sail_understory_refl,
                                        self.sail_inf_refl, self.sail_tts_trans, self.sail_tto_trans)

        return inform


# The "SetupMultiple" class handles management of LUT creations; it distributes input parameter ranges into actual
# Arrays that are later fed into PROSAIL in blocks (vectorized)
class SetupMultiple:

    def __init__(self, ns, paras, depends):
        self.whichlogicals = []  # list of all parameters with a logical distribution (start, stop, steps)
        self.nruns_logic_geo, self.nruns_logic_no_geo, self.nruns_logic_total = (1, 1, 1)

        # self.para_nums: defines the order in which PROSAIL results are placed in the LUT; this order is written
        # into the .lut-Meta file, so that the inversion algorithm knows, where to look for the paras
        # Like: "LAI" is at position 9 in the LUT
        self.para_nums = {"N": 0, "cab": 1, "car": 2, "anth": 3, "cbrown": 4, "cw": 5, "cm": 6, "cp": 7, "cbc": 8,
                          "LAI": 9, "typeLIDF": 10, "LIDF": 11, "hspot": 12, "psoil": 13, "tts": 14, "tto": 15,
                          "psi": 16, "LAIu": 17, "cd": 18, "sd": 19, "h": 20}

        self.npara = len(self.para_nums)  # how many parameters are part of the LUT? Notice that these are not the
                                          # parameters actually USED in the PROSAIL-version, but they are still STORED
                                          # e.g. "cbrown" is not part of prospect-4, but it is still in the LUT as
                                          # "None" or 0, so npara is the number of parameters that are currently used
                                          # for any of the PROSPECT / SAIL versions

        self.depends = depends  # should Car be calculated in dependence to cab?
        self.paras = paras  # paras are input of this class as a dictionary (**kwargs)
        self.ns = int(ns)  # ns: number of statistical distributions; i.e. "draw #ns times from the distribution"
        self.error_array = []

    def create_grid(self):
        # Each parameter in self.paras has four possible lengths:
        # len(para_key) == 1: parameter is fixed to ONE value
        # len(para_key) == 2: uniform distribution (min, max)
        # len(para_key) == 3: logical distribution (start, stop, nsteps)
        # len(para_key) == 4: statistical gauss (min, max, mean, std)
        # Depending on this, the full grid of input-parameters is filled as follows:

        # 1.1 find logically distributed parameters
        for para_key in self.paras:
            if len(self.paras[para_key]) == 3:  # logical distr. = min, max, nsteps
                self.whichlogicals.append(para_key)  # append parameter to the list of logically distributed paras

        # 1.2 calculate nruns_logical for each logically distributed parameter; result is a dictonary that contains
        # the number of logical steps for each parameter, e.g. {"tts": 5, "tto": 11, "psi": 19}
        self.nruns_logic = dict(zip(self.whichlogicals, [int(self.paras[para_key][2])
                                                         for para_key in self.whichlogicals]))

        # 1.3 calculate total nruns_logical
        for para_key in self.whichlogicals:
            if para_key in ["tts", "tto", "psi"]:
                self.nruns_logic_geo *= self.nruns_logic[para_key]  # contains only geometry
            else:
                self.nruns_logic_no_geo *= self.nruns_logic[para_key]  # contains everything except geometry
        self.nruns_logic_total = self.nruns_logic_geo * self.nruns_logic_no_geo

        # 2 Calculate total nruns
        self.nruns_total = int(self.nruns_logic_total * self.ns)  # ns draws from distribution * logical steps in total

        # 3 Create numpy array to hold all parameter constellations
        self.para_grid = np.empty(shape=(self.nruns_total, self.npara), dtype=np.float32)

        # 4 Fill each parameter into numpy array
        k = 0  # iterator for logical order
        self.repeat_accum = self.ns  # initialize value for "accumulated repetition of variable"

        # the functions "self.uniform_distribution", "self.gauss_distribution", "self.logical_distribution" manage
        # the stacking, repeating, cloning etc. of input parameter into the large self.para_grid
        for para_key in self.paras:
            if len(self.paras[para_key]) == 2:  # uniform distribution
                self.para_grid[:, self.para_nums[para_key]] = self.uniform_distribution(para_name=para_key,
                                                                                        min=self.paras[para_key][0],
                                                                                        max=self.paras[para_key][1],
                                                                                        multiply=self.nruns_logic_total)

            elif len(self.paras[para_key]) == 4:  # gaussian distribution
                self.para_grid[:, self.para_nums[para_key]] = self.gauss_distribution(para_name=para_key,
                                                                                      min=self.paras[para_key][0],
                                                                                      max=self.paras[para_key][1],
                                                                                      mean=self.paras[para_key][2],
                                                                                      sigma=self.paras[para_key][3],
                                                                                      multiply=self.nruns_logic_total)

            elif len(self.paras[para_key]) == 1:  # fixed parameter
                self.para_grid[:, self.para_nums[para_key]] = np.tile(self.paras[para_key][0], self.nruns_total)

            elif len(self.paras[para_key]) == 3:  # logically distributed parameter
                k += 1
                self.repeat_accum *= self.nruns_logic[para_key]  # how often do all ns-distributed parameters need to be
                                                                 # repeated? Once for each parameter with logical dist.
                multiply = self.nruns_total // self.repeat_accum
                self.para_grid[:, self.para_nums[para_key]] = self.logical_distribution(para_name=para_key,
                                                                                        min=self.paras[para_key][0],
                                                                                        max=self.paras[para_key][1],
                                                                                        repeat=self.repeat_accum /
                                                                                               self.nruns_logic[
                                                                                                   para_key],
                                                                                        multiply=multiply,
                                                                                        nsteps=self.paras[para_key][2])

            if self.depends == 1 and para_key == 'car':
                self.para_grid[:, self.para_nums[para_key]] = \
                    self.car_cab_dependency(grid=self.para_grid[:, self.para_nums['cab']])  # set car according to cab

        return self.para_grid

    def fixed(self, para_name, value):
        return_list = np.linspace(start=value, stop=value, num=self.ns)
        return return_list

    def logical_distribution(self, para_name, min, max, repeat, multiply, nsteps):
        # This is a complicated mix of repeating and tiling with Numpy to achieve the logical distribution
        # np.tile([0, 1, 2], 2) -> [0, 1, 2, 0, 1, 2]  # tile 'multiply' times
        # np.repeat(3, 4) -> [3, 3, 3, 3]              # repeat 'repeat' times
        return_list = np.tile(np.repeat(np.linspace(start=min, stop=max, num=int(nsteps)), repeat), multiply)
        return return_list

    def gauss_distribution(self, para_name, min, max, mean, sigma, multiply):
        # gauss_distribution is truncated with min and max! Tiling, see above
        try:
            return_list = np.tile(truncnorm((min - mean) / sigma, (max - mean) / sigma, loc=mean, scale=sigma).
                                  rvs(self.ns), multiply)
        except:
            raise ValueError("Cannot create gaussian distribution for parameter {}}. Check values!".format(para_name))
        return return_list

    def uniform_distribution(self, para_name, min, max, multiply):
        try:
            return_list = np.tile(np.random.uniform(low=min, high=max, size=self.ns), multiply)
        except:
            raise ValueError("Cannot create uniform distribution for parameter %s. Check values!" % para_name)
        return return_list

    def car_cab_dependency(self, grid):

        def truncated_noise(y, lower, upper):
            while True:
                y_noise = np.random.laplace(loc=0, scale=spread, size=1) + y
                if upper > y_noise > lower:
                    return y_noise

        def refine_noise(y, y_lin_noise, lower, upper):
            for i in range(len(y_lin_noise)):
                if upper[i] < y_lin_noise[i] or lower[i] > y_lin_noise[i]:
                    y_lin_noise[i] = truncated_noise(y[i], lower[i], upper[i])
            return y_lin_noise

        # constants from ANGERS03 Leaf Optical Data
        slope = 0.2234
        intercept = 0.9861
        spread = 4.6839
        car_lin = slope * grid + intercept
        lower_car = slope / spread * 3 * grid
        upper_car = slope * spread / 3 * grid + 2 * intercept

        car_lin_noise = np.random.laplace(loc=0, scale=spread, size=len(car_lin)) + car_lin
        car_lin_noise = refine_noise(car_lin, car_lin_noise, lower_car, upper_car)
        car_lin_noise = refine_noise(car_lin, car_lin_noise, lower_car, upper=np.tile(26, len(grid)))

        return car_lin_noise


# The class "Init_Model" initializes the models
class InitModel:

    # __init__ contains default values, but it is recommended to provide actual values for it
    def __init__(self, lop="prospectD", canopy_arch=None, int_boost=1, nodat=-999, s2s="default"):
        self._dir = os.path.dirname(os.path.realpath(__file__))  # get current directory
        os.chdir(self._dir)  # change into current directory
        self.lop = lop
        self.canopy_arch = canopy_arch
        self.int_boost = int_boost  # boost [0...1] of PROSAIL, e.g. int_boos = 10000 -> [0...10000] (EnMAP-default!)
        self.nodat = nodat
        self.s2s = s2s  # which sensor type? Default = Prosail out; "EnMAP", "Sentinel2", "Landsat8" etc.
        self.geo_mode = None  # "sort" (LUT contains multiple geos) vs. "no geo" (LUT contains ONE Geo)
        self.soil = None  # initialize empty

        # List of names of all parameters in order in which they are written into the LUT; serves as labels for output
        self.para_names = ["N", "cab", "car", "anth", "cbrown", "cw", "cm", "cp", "cbc",
                          "LAI", "typeLIDF", "LIDF", "hspot", "psoil", "tts", "tto",
                          "psi", "LAIu", "cd", "sd", "h"]

    def initialize_multiple_simple(self, soil=None, **paras):
        # simple tests for vectorized versions
        self.soil = soil
        nparas = len(paras['LAI'])
        para_grid = np.empty(shape=(nparas, len(paras.keys())))
        for run in range(nparas):
            for ikey, key in enumerate(self.para_names):
                para_grid[run, ikey] = paras[key][run]

        self.run_model(paras=dict(zip(self.para_names, para_grid.T)))

    def initialize_vectorized(self, LUT_dir, LUT_name, ns, max_per_file=5000, soil=None,
                            prgbar_widget=None, qgis_app=None, depends=False, testmode=False, **paras):
        # This is the most important function for initializing PROSAIL
        # It calls instances of PROSAIL and provides blocks of the para_grid
        self.soil = soil
        if len(paras["tts"]) > 1 or len(paras["tto"]) > 1 or len(paras["psi"]) > 1:
            self.geo_mode = "sort"  # LUT-Files are (firstly) sorted by geometry
        else:
            self.geo_mode = "no_geo"

        self.max_filelength = max_per_file  # defines the number of PROSAIL runs in one file ("split"), default=5000
        npara = len(self.para_names)  # how many parameters are stored in the LUT
                                      # (at maximum! Does NOT depend on the version of PROSPECT / SAIL used)
        setup = SetupMultiple(ns=ns, paras=paras, depends=depends)  # Prepare for setting up PROSAIL
        para_grid = setup.create_grid()  # Now create the para_grid

        crun_max = setup.nruns_total  # The total number of PROSAIL executions
        crun_pergeo = setup.ns * setup.nruns_logic_no_geo  # The number of PROSAIL executions
                                                           # per geometrical constellation

        n_ensembles_split, n_ensembles_geo = (1, 1)  # initialize ensembles

        if self.geo_mode == "sort":
            n_ensembles_geo = setup.nruns_logic_geo
        elif self.geo_mode == "no_geo":
            n_ensembles_geo = 1

        if crun_pergeo <= max_per_file:  # exactly one LUT-file per Geo
            n_ensembles_split = 1
        else:  # second split: several files per Geo
            n_ensembles_split = (crun_pergeo - 1) // max_per_file + 1  # number of ensembles
                                                                       # (=number of LUT-files to create)

        if not self.s2s == "default":
            # Initialize Spec2Sensor to convert PROSAIL output
            self.s2s_I = Spec2Sensor(sensor=self.s2s, nodat=self.nodat)
            sensor_init_success = self.s2s_I.init_sensor()
            if not sensor_init_success:
                exit("Could not convert spectra to sensor resolution!")
            nbands = self.s2s_I.n_wl_sensor
            wl_sensor = self.s2s_I.wl_sensor
        else:
            nbands = len(lambd)
            wl_sensor = lambd

        # for debugging or time estimation
        if testmode == True:
            start = time.time()
            _ = self.run_model(paras=dict(zip(self.para_names, para_grid.T))).T  # simplistic form of running PROSAIL
            return time.time() - start

        # Initialize iterators
        struct_ensemble = 0
        n_struct_ensembles = 1

        ##  Prepare content for .lut-metafile:
        # Geometries are either logical (len == 3) or fixed (len == 1) or not supplied
        if len(paras["tts"]) == 3:
            tts_fl = np.linspace(start=setup.paras["tts"][0], stop=setup.paras["tts"][1],
                                 num=int(setup.paras["tts"][2]))
            tts_str = [tts_fl.astype(str)[i] for i in range(len(tts_fl))]
        elif len(paras["tts"]) == 1:
            tts_str = [str(paras["tts"][0])]
        else:
            tts_str = ["NA"]

        if len(paras["tto"]) == 3:
            tto_fl = np.linspace(start=setup.paras["tto"][0], stop=setup.paras["tto"][1],
                                 num=int(setup.paras["tto"][2]))
            tto_str = [tto_fl.astype(str)[i] for i in range(len(tto_fl))]
        elif len(paras["tto"]) == 1:
            tto_str = [str(paras["tto"][0])]
        else:
            tto_str = ["NA"]

        if len(paras["psi"]) == 3:
            psi_fl = np.linspace(start=setup.paras["psi"][0], stop=setup.paras["psi"][1],
                                 num=int(setup.paras["psi"][2]))
            psi_str = [psi_fl.astype(str)[i] for i in range(len(psi_fl))]
        elif len(paras["psi"]) == 1:
            psi_str = [str(paras["psi"][0])]
        else:
            psi_str = ["NA"]

        # Name of the metafile is defined by name of the LUT + _00meta and has the extension of .lut
        with open("%s_00meta.lut" % (LUT_dir + LUT_name), "w") as meta:
            meta.write("name=%s" % LUT_name)
            meta.write("\nn_total=%i" % setup.nruns_total)
            meta.write("\nns=%i" % setup.ns)
            meta.write("\nlop_model=%s" % self.lop)
            meta.write("\ncanopy_architecture_model=%s" % self.canopy_arch)
            meta.write("\ngeo_mode=%s" % self.geo_mode)
            meta.write("\ngeo_ensembles=%i" % n_ensembles_geo)
            meta.write("\nsplits=%i" % n_ensembles_split)
            meta.write("\nmax_file_length=%i" % self.max_filelength)
            meta.write("\ntts={}".format(";".join(i for i in tts_str)))
            meta.write("\ntto={}".format(";".join(i for i in tto_str)))
            meta.write("\npsi={}".format(";".join(i for i in psi_str)))
            meta.write("\nmultiplication_factor=%i" % self.int_boost)
            meta.write("\nparameters={}".format(";".join(i for i in self.para_names)))
            meta.write("\nwavelengths={}".format(";".join(str(i) for i in wl_sensor)))

        # Write another metafile which contains the ranges of all parameters (for information and restoring in the GUI)
        with open("%s_00paras.txt" % (LUT_dir + LUT_name), "w") as paras_meta:
            paras_meta.write("name=%s" % LUT_name)
            paras_meta.write("\nlop_model=%s" % self.lop)
            paras_meta.write("\ncanopy_architecture_model=%s" % self.canopy_arch)
            paras_meta.write("\nCab-Car-Dependency={:d}# Dependency is {}".format(depends, bool(depends)))
            for para_key in self.para_names:
                if len(paras[para_key]) == 1:  # fixed
                    paras_meta.write("\n{}={}# Fixed value = {:f}"
                                     .format(para_key, paras[para_key], paras[para_key][0]))
                elif len(paras[para_key]) == 2:  # uniform
                    paras_meta.write("\n{}={}# Uniform statistical distribution with min={:f}, max={:f}"
                                     .format(para_key, paras[para_key], paras[para_key][0], paras[para_key][1]))
                elif len(paras[para_key]) == 3:  # logical
                    paras_meta.write("\n{}={}# Logical numerical distribution with min={:f}, max={:f}, steps={:d}"
                                     .format(para_key, paras[para_key], paras[para_key][0], paras[para_key][1],
                                             int(paras[para_key][2])))
                elif len(paras[para_key]) == 4:  # gauss
                    paras_meta.write("\n{}={}# Gauss-normal statistical distribution with min={:f}, max={:f}, "
                                     "mean={:f}, std={:f}"
                                     .format(para_key, paras[para_key], paras[para_key][0], paras[para_key][1],
                                             paras[para_key][2], paras[para_key][3]))

        # Set text of the progress bar (if this script is run in the EnMAP-box
        if prgbar_widget:
            prgbar_widget.gui.lblCaption_l.setText("Creating LUT")
            qgis_app.processEvents()

        for geo_ensemble in range(n_ensembles_geo):  # iterate through all ensembles of geometries
            rest = crun_pergeo
            for split in range(n_ensembles_split):  # iterate through all "splits" (max_per_file)

                if rest >= max_per_file:  # if there are more runs left than max_per_file allows...
                    save_array = np.empty((nbands + npara, max_per_file))  # build an empty array
                    nruns = max_per_file  # runs is max
                else:
                    nruns = rest  # otherwise, nruns is what's left
                    save_array = np.empty((nbands + npara, rest))

                run = geo_ensemble * crun_pergeo + split * max_per_file  # current run (first of the current split)

                if prgbar_widget:
                    if prgbar_widget.gui.lblCancel.text() == "-1":
                        prgbar_widget.gui.lblCancel.setText("")
                        prgbar_widget.gui.cmdCancel.setDisabled(False)
                        raise ValueError("LUT creation cancelled!")

                    prgbar_widget.gui.lblCaption_r.setText('Ensemble Geo {:d} of {:d} | Split {:d} of {:d}'.
                                                           format(geo_ensemble + 1, n_ensembles_geo, split+1,
                                                                  n_ensembles_split))
                    qgis_app.processEvents()

                else:
                    print(
                        "LUT ensemble struct #{:d} of {:d}; ensemble geo #{:d} of {:d}; split #{:d} of {:d}; "
                        "total #{:d} of {:d}"
                        .format(struct_ensemble, n_struct_ensembles - 1, geo_ensemble,
                                n_ensembles_geo - 1, split, n_ensembles_split - 1, run, crun_max))

                if prgbar_widget:
                    prgbar_widget.gui.prgBar.setValue(int(run * 100 / crun_max))  # set value of the progress bar
                    qgis_app.processEvents()

                # Execute the model and fill the results into the prepared array
                # The double transpose of the matrix (.T) fits the paras in the necessary shape run_model expects
                # The first "npara" rows are reserved for the parameter-values
                # The rest is reserved for the spectral results of PROSAIL
                save_array[npara:, :] = self.run_model(paras=
                                                       dict(zip(self.para_names, para_grid[run:run + nruns, :].T))).T
                save_array[:npara, :] = para_grid[run:run + nruns, :].T

                rest -= max_per_file  # calculate what's left for next iteration

                # Save each split to a new file (.npy)
                np.save("{}_{:d}_{:d}".format(LUT_dir + LUT_name, geo_ensemble, split), save_array)

        if prgbar_widget:
            prgbar_widget.gui.lblCaption_r.setText('File {:d} of {:d}'.format(crun_max, crun_max))
            prgbar_widget.gui.prgBar.setValue(100)
            prgbar_widget.gui.close()

    def initialize_single(self, **paras):
        # Initialize a single run of PROSAIL (simplification for building of para_grid)
        self.soil = paras["soil"]
        if not self.s2s == "default":
            self.s2s_I = Spec2Sensor(sensor=self.s2s, nodat=self.nodat)
            sensor_init_success = self.s2s_I.init_sensor()
            if not sensor_init_success:
                exit("Could not convert spectra to sensor resolution!")

        para_grid = np.empty(shape=(1, len(paras.keys())))  # shape 1 for single run
        for ikey, key in enumerate(self.para_names):
            para_grid[0, ikey] = paras[key]
        return self.run_model(paras=dict(zip(self.para_names, para_grid.T)))

    def run_model(self, paras):
        # Execution of PROSAIL
        i_model = CallModel(soil=self.soil, paras=paras)  # Create new instance of CallModel

        # 1: Call one of the Prospect-Versions
        if self.lop == "prospect4":
            i_model.call_prospect4()
        elif self.lop == "prospect5":
            i_model.call_prospect5()
        elif self.lop == "prospect5B":
            i_model.call_prospect5b()
        elif self.lop == "prospectD":
            i_model.call_prospectD()
        elif self.lop == "prospectPro":
            i_model.call_prospectPro()
        else:
            print("Unknown Prospect version. Try 'prospect4', 'prospect5', 'prospect5B' or 'prospectD' or ProspectPro")
            return

        # 2: If chosen, call one of the SAIL-versions and multiply with self.int_boost
        if self.canopy_arch == "sail":
            result = i_model.call_4sail() * self.int_boost
        elif self.canopy_arch == "inform":
            result = i_model.call_inform() * self.int_boost
        else:
            result = i_model.prospect[:, :, 1] * self.int_boost

        if self.s2s == "default":
            return result
        else:
            return self.s2s_I.run_srf(result)  # if a sensor is chosen, run the Spectral Response Function now
