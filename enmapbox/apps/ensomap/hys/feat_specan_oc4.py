# -*- coding: utf-8 -*-
#
# Copyright © 2019 Stéphane Guillaso
# Licensed under the terms of 
# (see ../../LICENSE.md for details)

import numpy as np
import hys
import numba as nb

__bands__    = [478, 546, 659]
__filename__ = "_OC_VISonly_478_546_659"
__gui__      = "SOC Index: R478 / (R659 * R546)"
__info__     = "Organic carbon content: \n"+\
    "Calculate a SOC index based solely on visible wavelengths: \n\n"+\
    "ind = R_478 / (R_659 * R_546)\n\n"+\
    "Thaler, E.A., Larsen, I.J., Yu, Q., 2019. \n"+\
    "A new index for remote sensing of soil organic carbon based \n"+\
    "solely on visible wavelengths. \n"+\
    "Soil Sci. Soc. Am. J. 83 (5), 1443–1450."

def check_bands(ubands, wvl):
    ind0 = int(ubands[0])
    ind1 = int(ubands[1])
    ind2 = int(ubands[2])
    if len(list(set((ind0, ind1, ind2)))) < 3:
        return False, 'Identical band found!\n'
    if (ind1-ind0) < 2 or (ind2-ind1) < 2:
        return False, 'Not enough points to calculate crad!\n'
    return True, "Has been calculated!\n"


@nb.jit(nb.float32[:,:](nb.float32[:,:,:], nb.float32[:], nb.int32[:], nb.int32[:,:]), nopython=True, fastmath=True)
def process(cube, wvl, ind, mask):
    ny = cube.shape[1]
    nx = cube.shape[2]
    out = np.zeros((ny, nx), dtype=np.float32)
    for ky in range(ny):
        for kx in range(nx):
            if mask is not None:
                if mask[ky, kx] == 0:
                    out[ky, kx] = np.nan
                    continue
            R478 = cube[ind[0], ky, kx]
            R546 = cube[ind[1], ky, kx]
            R659 = cube[ind[2], ky, kx]
            tmp = R659 * R546
            if tmp != 0: out[ky, kx] = R478 / tmp
            else:        out[ky, kx] = np.nan
    return out
