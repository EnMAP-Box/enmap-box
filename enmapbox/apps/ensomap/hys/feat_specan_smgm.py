# -*- coding: utf-8 -*-
#
# Copyright © 2019 Stéphane Guillaso
# Licensed under the terms of 
# (see ../../LICENSE.md for details)

import numpy as np
import hys
import os # <-- to be removed
# import importlib
import numba as nb

__bands__    = [500, 2410, 2390]
__filename__ = "_MOISTURE_SMGM"
__gui__      = "Soil Moisture Gaussian Model (SMGM)"
__info__     = "Estimate the soil moisture content by using a Gaussian model.\n\n"+\
    "Whiting, M.L., Li, L., Ustin, S.L., 2004.\n"+\
    "Predicting water content using Gaussian model on soil spectra.\n"+\
    "Remote Sens. Environ. 89, 535–552."
    
# def check_bands(ubands, wvl):
#     ind0 = int(ubands[0])
#     ind1 = int(ubands[1])
#     if ind0 == ind1:
#         return False, 'Identical band found!\n'
#     if (ind1-ind0) < 2:
#         return False, 'Not enough points to calculate crad!\n'
#     return True, "Has been calculated!\n"


# @nb.jit(nopython=True)
# def process(cube, wvl):
#     ny = cube.shape[1]
#     nx = cube.shape[2]
#     out = np.zeros((ny, nx), dtype=np.float32)
#     for ky in range(ny):
#         for kx in range(nx):
#             out[ky, kx] = hys.tools.get_crad(wvl, cube[:, ky, kx])
#     return out
