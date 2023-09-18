# Here is a collection of tools
#
# (c) Dr. Stéphane Guillaso 2019

from numba import jit, float32, void, intc, int64, int32
import numpy as np

#   This routine calculate the continuum line to be removed from the original spectrum.
#   It is a recursive routine.
#
#   Algo: 
#   1) calculate the line equation between the extreme points of the spectrum y
#     we obtain 2 coefficients: a and b
#   2) calculate the continumm line h between extreme points
#     h = a * x + b
#   3) calculate distance from each spectrum position to the line dlm
#   4) we choose the lowest value corresponding the the biggest distance between
#      line and a point above the line (this is due to the calculation line-point)
#   5) Test this distance
#     - if dlm >= 0 then we exit the routine, meaning that we don't have any point
#       above the line
#   6) We split the spectrum into 2 parts at the position of the selected point
#      (dlp)
#   7) We call the same routine over the 2 sub lines and we continue.
#
#   This routines is based on the algorithm described here:
#   https://en.wikipedia.org/wiki/Quickhull
#   the main difference is that we calculate only the upper part (as we are not 
#   interesting to the lower part of the spectrum)
# 
#   At the end, the variable h (having the same size than x and y) is returning
#   the continuum line.


@jit(void(float32[:], float32[:], float32[:], intc, intc), nopython=True, fastmath=True)
def get_continuum_line(x, y, h, beg, end):
    
    a = (y[end] - y[beg]) / (x[end] - x[beg])
    b = y[beg] - a * x[beg]

    dlv = 0.
    dlm = 10000.
    dlp = -1

    for k in range(beg, end+1, 1):
        h[k] = a * x[k] + b
        dlv = (a * x[k] - y[k] + b) / np.sqrt(a*a + 1)
        if (dlv<dlm):
            dlm = dlv
            dlp = k
    
    if (dlm == 0): return
    if (dlp > beg and dlp < end):
        get_continuum_line(x, y, h, beg, dlp)
        get_continuum_line(x, y, h, dlp, end)


# This routine is calcualte the continuum removal absorption depth based on the
# Clark's quota approach.
# 
# input: 
# - x corresponds to an array containing the wavelength
# - y corresponds to the reflectance at the given wavelengths
# - nx is the size of the input arrays
# x and y should have the same size (nx)

@jit(float32(float32[:], float32[:]), nopython=True, fastmath=True)
def get_crad(x, y):
    
    # calculate the continuum line (h)
    nx = x.shape[0]
    h = np.zeros(nx, dtype=np.float32)
    get_continuum_line(x, y, h, 0, nx-1)

    # calculate the Clark's quota
    qmax = -99999
    for k in np.arange(0, nx):
        if h[k] != 0:
            q = 1. - y[k]/h[k]
            if q > qmax:
                qmax = q
    # return the value
    if qmax == -99999: qmax = np.nan
    return qmax


@jit(int64[:](int32, int32, float32[:], intc[:], intc, intc), nopython=True, fastmath=True)
def coord2points(xpos, ypos, map_info, dim, win, opt):
    x = 0.
    y = 0.
    if opt != 0:
        x = xpos - 1
        y = ypos - 1
    else:
        x0    = np.float32(map_info[1]) - 1
        y0    = np.float32(map_info[2]) - 1
        xref  = np.float32(map_info[3])
        yref  = np.float32(map_info[4])
        xstep = np.float32(map_info[5])
        ystep = np.float32(map_info[6])
        x = np.abs(xpos - xref) / xstep + x0
        y = np.abs(ypos - yref) / ystep + y0
    out = np.zeros((4), dtype = np.int64)
    xmin = np.int64(x - win/2)
    xmax = np.int64(x + win/2)
    ymin = np.int64(y - win/2)
    ymax = np.int64(y + win/2)
    if xmin < 0: xmin = 0
    if xmax > dim[0]: xmax = dim[0]
    if ymin < 0: ymin = 0
    if ymax > dim[1]: ymax = dim[1]

    out[0] = xmin
    out[1] = xmax
    out[2] = ymin
    out[3] = ymax

    return out

