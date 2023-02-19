#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
***************************************************************************
    engeomap.py

This is EnGeoMAP further information can be found in the following open acess publication:
Mielke, C.; Rogass, C.; Boesche, N.; Segl, K.; Altenberger, U. 
EnGeoMAP 2.0�Automated Hyperspectral Mineral Identification for the German EnMAP Space Mission. 
Remote Sens. 2016, 8, 127. 
    ---------------------
    Date                 : Juli 2019
    Copyright            : (C) 2019 by Christian Mielke
    Email                : christian.mielke@gfz-potsdam.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Changelog
EnGeoMAP Version 3.2
Date: February 2023
Author: Helge L. C. Daempfling
Email: hdaemp@gfz-potsdam.de

The following modifications to the EnGeoMAP 3.1 release were realized:

- console output added and modified to indicate stage of
calculations of EnGeoMAP.

- data output names were changed for more clarity
(see algorithms.py)

"""

import copy
import os

import numpy
from osgeo import gdal
from osgeo import gdalnumeric
from scipy import interpolate
from scipy import ndimage
from scipy import optimize
from scipy import signal
from scipy import spatial

# from engeomap import APP_DIR


##### I need this to parse header inforation:
###########
def return_header(filename):
    with open(filename, 'r') as file:
        h = file.readlines()
    j = []
    g = ''
    for i in h:
        i = i.replace('\n', '')
        i = i.replace('\r\n', '')
        g = g + i
        if ('{' and '}' in g) or ('=' and '{' not in g):
            j.append(g)
            g = ''
    return j


def return_header_list(filename):
    with open(filename, 'r') as file:
        h = file.readlines()
    j = []
    g = ''
    for i in h:
        g = g + i
        if ('{' and '}' in g) or ('=' and '{' not in g):
            j.append(g)
            g = ''
    return j


def splitter_hd(liste):
    hd_liste = {}
    prp = []
    val = []
    for i in liste:
        if '=' in i:
            i = i.replace('{', '')
            i = i.replace('}', '')
            i = i.replace('\r', '')
            i = i.replace('\r\n', '')
            i = i.replace('\n', '')
            i = i.strip()
            i = i.split('=')
            i[0] = i[0].strip()
            i[1] = i[1].strip()
            prp.append(i[0])
            val.append(i[1])
            hd_liste.update({i[0]: i[1]})
    w = hd_liste.keys()
    return hd_liste, w, prp, val


def splitter_hd2(liste):
    hd_liste = {}
    prp = []
    val = []
    for i in liste:
        if '=' in i:
            i = i.replace('{', '')
            i = i.replace('}', '')
            i = i.replace('\r', '')
            i = i.replace('\r\n', '')
            i = i.replace('\n', '')
            i = i.strip()
            i = i.split('=')
            i[0] = i[0].strip()
            i[1] = i[1].strip()
            prp.append(i[0])
            try:
                val.append(float(i[1]))
            except(ValueError):
                val.append(i[1])
            hd_liste.update({i[0]: i[1]})
    w = hd_liste.keys()
    return hd_liste, w, prp, val


class read_hdr(object):
    def __init__(self, filename=None):
        if type(filename) == str:
            self.filename = filename
            self.r_h = return_header(self.filename)
            self.obj = splitter_hd(self.r_h)
            self.li = self.obj[1]
            self.di = self.obj[0]
            self.prp = self.obj[2]
            self.val = self.obj[3]
            for i in self.li:
                setattr(self, i.replace(' ', '_'), self.di.get(i))

    def make_liste_w(self):
        pass


def str2npar(string):
    ah = string.split(',')
    data = numpy.asarray(ah)
    data = data.astype(float)
    return data


class read_hdr_flt(object):  # Read in Header and give its values back as floats
    def __init__(self, filename=None):
        if type(filename) == str:
            self.filename = filename
            self.r_h = return_header(self.filename)
            self.obj = splitter_hd(self.r_h)
            self.li = self.obj[1]
            self.di = self.obj[0]
            self.prp = self.obj[2]
            self.val = self.obj[3]
            for i in self.li:
                try:
                    setattr(self, i.replace(' ', '_'), float(self.di.get(i)))
                except(ValueError):
                    setattr(self, i.replace(' ', '_'), self.di.get(i))
            try:
                self.wavelength
                if type(self.wavelength) == str:
                    self.wavelength = str2npar(self.wavelength)
            except(AttributeError):
                pass
            try:
                self.Wavelength
                if type(self.Wavelength) == str:
                    self.Wavelength = str2npar(self.Wavelength)
            except(AttributeError):
                pass
            try:
                self.fwhm
                if type(self.fwhm) == str:
                    self.fwhm = str2npar(self.fwhm)
            except(AttributeError):
                pass
            try:
                self.bbl
                if type(self.bbl) == str:
                    self.bbl = str2npar(self.bbl)
            except(AttributeError):
                pass

    def make_liste_w(self):
        pass


########################
############################
# Header Parsing FInished!
###############################

#########I need these functions to prepare the data
################


def check_load_data(bild):
    bildh = os.path.basename(bild)
    print('...loading '+bildh)
    try:
        data = gdalnumeric.LoadFile(bild)
    except Exception:
        print("No data load possible! Please check the Files and headers (.hdr)!")
        print("EnGeoMAP execution halted! Please restart the Application.")
    data = data.astype(float)
    if '.' in bild:
        bild = bild.split('.')[0]
    hdd = read_hdr_flt(bild + '.hdr')
    try:
        wavelength = hdd.wavelength
    except AttributeError:
        wavelength = hdd.Wavelength
    if numpy.max(wavelength) < 30:
        wavelength *= 1000
    if numpy.max(data) < 10:
        print("The image data will be scaled x10k for processing.")
        data *= 10000.0
    maxx = numpy.trunc(numpy.max(wavelength))
    minn = numpy.trunc(numpy.min(wavelength))
    nwav1nm = numpy.arange(minn, maxx, 1)
    return wavelength, nwav1nm, data

def compare_wavelengths(wvlib, wvbild):
    print('...comparing wavelengths...')
    minbild = wvbild.min()
    maxbild = wvbild.max()
    minlib = wvlib.min()
    maxlib = wvlib.max()
    if minlib <= minbild:
        minn = minbild
        minflag = 1
    else:
        minn = minlib
        minflag = 0
    if maxlib <= maxbild:
        maxx = maxbild
        maxflag = 0
    else:
        maxx = maxlib
        maxflag = 1
    if maxflag == 1 and minflag == 1:
        print('Spectral range of image data and library is matching: No clipping needed.')
    else:
        print('Spectral range of image data larger than the used library entries: Data must be be clipped!')
    return minn, maxx, minflag, maxflag


# returns shortest intersecting wvl rage for 1nm interpolation

def prep_1nm_interpol_intersect(minn, maxx, minflag, maxflag, w1nmlib, w1nmbild):
    print('...interpolating...')
    if minflag * maxflag == 1:
        maximum = numpy.max(w1nmbild)
        minimum = numpy.min(w1nmbild)
    elif minflag == 1 and maxflag == 0:
        minimum = numpy.min(w1nmbild)
        maximum = numpy.max(w1nmlib)
    elif minflag == 0 and maxflag == 1:
        minimum = numpy.max(w1nmbild)
        maximum = numpy.min(w1nmlib)
    elif minflag == 0 and maxflag == 0:
        maximum = numpy.max(w1nmlib)
        minimum = numpy.min(w1nmlib)
    return numpy.arange(minimum, maximum, 1)


#########
##########Data Preparation Finished
##################

###
# misc interpolation functions for the spectra:
#########

def interpolate_generic1nmlib(wv, data):
    neowave = numpy.arange(numpy.trunc(min(wv)), numpy.trunc(max(wv)), 1)
    arr = numpy.zeros([data.shape[0], len(neowave)])
    for j in numpy.arange(0, data.shape[0], 1):
        interpolator = interpolate.splrep(wv, data[j, :], s=0)
        arr[j, :] = interpolate.splev(neowave, interpolator, der=0)
    return arr, neowave


def interpolate_1nm_spectrum(wvto, wvfrom, data, flag=None):
    wvid = numpy.unique(wvfrom, return_index=True)
    wvfrom = wvfrom[wvid[1]]
    data = data[wvid[1]]
    if (flag == 1) & (numpy.max(wvto < 1290)):
        output = numpy.ones([len(wvto)], dtype='float')
        interpolator = interpolate.splrep(wvfrom, data, s=0)
        output = interpolate.splev(wvto, interpolator, der=0)
        return output  # ,wvto,wvfrom
    if (flag != 1) & (numpy.max(wvto < 1290)):
        output = numpy.ones([len(wvto)], dtype='float')
        interpolator = interpolate.splrep(wvfrom, data, s=0)
        output = interpolate.splev(wvto, interpolator, der=0)
        return output  # ,wvto,wvfrom
    elif (flag == 1):
        output = numpy.ones([len(wvto)], dtype='float')
        interpolator = interpolate.splrep(wvfrom, data, s=0)
        output = interpolate.splev(wvto, interpolator, der=0)
        return output  # ,wvto,wvfrom
    if (flag != 1) & (numpy.max(wvto > 2100)):
        output = numpy.ones([len(wvto)], dtype='float')
        # Wasserbanden:
        f1 = [1290, 1450]
        f2 = [1750, 2010]
        vnir = numpy.where(wvfrom < f1[0])[0]
        swir1 = numpy.where((wvfrom > f1[1]) & (wvfrom < f2[0]))[0]
        swir2 = numpy.where(wvfrom > f2[1])[0]
        gapwave1 = (wvfrom[swir1[0]] - wvfrom[vnir[-1]]) / 2 + wvfrom[vnir[-1]]
        gapwave2 = (wvfrom[swir2[0]] - wvfrom[swir1[-1]]) / 2 + wvfrom[swir1[-1]]
        gapref1 = (data[vnir[-1]] / 2 + data[swir1[0]] / 2) / 2
        gapref2 = (data[swir1[-1]] / 2 + data[swir2[0]] / 2) / 2
        wv_from_neo = numpy.concatenate(
            (wvfrom[vnir], numpy.insert(wvfrom[swir1], 0, gapwave1), numpy.insert(wvfrom[swir2], 0, gapwave2)))
        data_neo = numpy.concatenate(
            (data[vnir], numpy.insert(data[swir1], 0, gapref1), numpy.insert(data[swir2], 0, gapref2)))
        interpolator = interpolate.splrep(wv_from_neo, data_neo, s=0)
        output = interpolate.splev(wvto, interpolator, der=0)
        return output  # ,wvto,wv_from_neo
    if (flag != 1) & (numpy.max(wvto < 1750)):
        output = numpy.ones([len(wvto)], dtype='float')
        # Wasserbanden:
        f1 = [1290, 1450]
        vnir = numpy.where(wvfrom < f1[0])[0]
        swir1 = numpy.where((wvfrom > f1[1]))[0]
        gapwave1 = (wvfrom[swir1[0]] - wvfrom[vnir[-1]]) / 2 + wvfrom[vnir[-1]]
        gapref1 = (data[vnir[-1]] / 2 + data[swir1[0]] / 2) / 2
        wv_from_neo = numpy.concatenate((wvfrom[vnir], numpy.insert(wvfrom[swir1], 0, gapwave1)))
        data_neo = numpy.concatenate((data[vnir], numpy.insert(data[swir1], 0, gapref1)))
        interpolator = interpolate.splrep(wv_from_neo, data_neo, s=0)
        output = interpolate.splev(wvto, interpolator, der=0)
        return output  # ,wvto,wv_from_neo
    else:
        #print("Error expected spectral library data (2d mat)")
        return None


def interpolate_generic1nmlib_nwave(wv, data, neowave, flag=0):
    # neowave=numpy.arange(numpy.trunc(min(wv)),numpy.trunc(max(wv)),1)
    arr = numpy.zeros([data.shape[0], len(neowave)])
    for j in numpy.arange(0, data.shape[0], 1):
        arr[j, :] = interpolate_1nm_spectrum(neowave, wv, data[j, :], flag)
    return arr, neowave


def interpolate_generic1nmlib_unique(wv, data):
    wvid = numpy.unique(wv, return_index=True)
    # return wvid
    wv = wv[wvid[1]]
    data = data[:, wvid[1]]
    neowave = numpy.arange(numpy.trunc(min(wv)), numpy.trunc(max(wv)) + 1, 1)
    arr = numpy.zeros([data.shape[0], len(neowave)])
    for j in numpy.arange(0, data.shape[0], 1):
        interpolator = interpolate.splrep(wv, data[j, :], s=0)
        arr[j, :] = interpolate.splev(neowave, interpolator, der=0)
    return arr, neowave


def prephdr(hdrobj):
    fg = []
    fg.append('bbl={' + hdrobj.bbl + '}\n')
    try:
        fg.append('wavelength={' + hdrobj.Wavelength + '}\n')
    except AttributeError:
        fg.append('wavelength={' + hdrobj.wavelength + '}\n')
    return fg


########
# End Misc Interpolation Functions
####

####
######Cvx Hull
##########


def cvx_uhull2(spc, wv, cont_switch=0):
    aux = numpy.zeros([len(wv), 2])
    aux[:, 0] = wv
    aux[:, 1] = spc
    objec = spatial.ConvexHull(aux)
    vert = objec.vertices
    delta = numpy.unique(vert)
    punt = numpy.interp(wv[delta], [wv[0], wv[-1]], [spc[0], spc[-1]])
    minus = spc[delta] - punt
    avas = numpy.where(minus >= 0)  #
    a1 = spc[delta[avas]]
    a2 = wv[delta[avas]]
    hullfinal = numpy.interp(wv, a2, a1)
    rmrel = numpy.nan_to_num(spc / hullfinal)
    rmabs = numpy.nan_to_num(hullfinal - spc)
    numpy.place(rmrel, rmrel > 1, 1)
    numpy.place(rmrel, rmrel < 0, 0)
    numpy.place(rmabs, rmabs < 0, 0)
    if cont_switch == 1:
        return rmabs, rmrel, hullfinal
    if cont_switch == 0:
        return rmabs, rmrel


def cvx_uhull3(spc, wv):
    aux = numpy.zeros([len(wv), 2])
    aux[:, 0] = wv
    aux[:, 1] = spc
    objec = spatial.ConvexHull(aux)
    vert = objec.vertices
    delta = numpy.unique(vert)
    punt = numpy.interp(wv[delta], [wv[0], wv[-1]], [spc[0], spc[-1]])
    minus = spc[delta] - punt
    avas = numpy.where(minus >= 0)
    a1 = spc[delta[avas]]
    a2 = wv[delta[avas]]
    hullfinal = numpy.interp(wv, a2, a1)
    return hullfinal

def sortierer(wv, wve):
    if wv[0] > wve:
        return 0, 0
    else:
        minni = numpy.argmin(numpy.abs(numpy.abs((numpy.ones_like(wv) * wve) - wv)))
        minimum = wv[minni]
        return 1, minimum, minni
    return 0, 0


def getrange(wv):
    schulterliste = [1300, 1450, 1800, 2010]
    indices = []
    minima = []
    for j in enumerate(schulterliste):
        d = sortierer(wv, j[1])
        if len(d) == 2:
            continue
        if len(d) > 2:
            indices.append(d[2])
            minima.append(d[1])
    return numpy.asarray([indices, minima])

def generic_1nm_data_feat_grabber(lneo, rneo, spec, wave):
    ww = numpy.where((wave >= lneo) & (wave <= rneo))
    return ww, spec[ww], wave[ww]


def cvx_hull(daten, wv, cont_switch=0):
    wv1 = copy.deepcopy(wv)
    schp = getrange(wv)
    indices = schp[0, :]
    well = schp[1, :]
    if len(well) == 4:
        vnirds = generic_1nm_data_feat_grabber(wv[0], schp[1, 0], daten, wv1)
        swir1ds = generic_1nm_data_feat_grabber(schp[1, 1], schp[1, 2], daten, wv1)
        swir2ds = generic_1nm_data_feat_grabber(schp[1, 1], wv1[-1], daten, wv1)
        vnirhull = cvx_uhull3(vnirds[1], vnirds[2])
        swir1hull = cvx_uhull3(swir1ds[1], swir1ds[2])
        swir2hull = cvx_uhull3(swir2ds[1], swir2ds[2])
        wavv = numpy.concatenate([vnirds[2], swir1ds[2], swir2ds[2]])
        huell = numpy.concatenate([vnirhull, swir1hull, swir2hull])
        hullfinal = numpy.interp(wv, wavv, huell)
        rmrel = numpy.nan_to_num(daten / hullfinal)
        rmabs = numpy.nan_to_num(hullfinal - daten)
        numpy.place(rmrel, rmrel > 1, 1)
        numpy.place(rmrel, rmrel < 0, 0)
        numpy.place(rmabs, rmabs < 0, 0)
    else:
        print('we need the full spectrum with full swir and not only a part')
    if cont_switch == 1:
        return rmabs, rmrel, hullfinal
    if cont_switch == 0:
        return rmabs, rmrel


def cvx_hull_oclip(wv, daten):
    wv1 = copy.deepcopy(wv)
    schp = getrange(wv)
    indices = schp[0, :]
    well = schp[1, :]
    if len(well) == 4:
        vnirds = generic_1nm_data_feat_grabber(wv[0], schp[1, 0], daten, wv1)
        swir1ds = generic_1nm_data_feat_grabber(schp[1, 1], schp[1, 2], daten, wv1)
        swir2ds = generic_1nm_data_feat_grabber(schp[1, 1], wv1[-1], daten, wv1)
        vnirhull = cvx_uhull3(vnirds[1], vnirds[2])
        swir1hull = cvx_uhull3(swir1ds[1], swir1ds[2])
        swir2hull = cvx_uhull3(swir2ds[1], swir2ds[2])
        wavv = numpy.concatenate([vnirds[2], swir1ds[2], swir2ds[2]])
        huell = numpy.concatenate([vnirhull, swir1hull, swir2hull])
        outp = numpy.interp(wv, wavv, huell)
    return outp


#########
############
########


###
###Calculate Feature Weights for EnGEoMAP
##########

def weighting_lib2(rm_rel, wav):
    w = copy.deepcopy(rm_rel)
    ww = copy.deepcopy(rm_rel)
    fwhm = wav - numpy.roll(wav, 1)
    fwhm[0] = fwhm[1]
    if numpy.sum(w) == 0:
        ww *= 0
        return w, ww
    lbls, nlbl = ndimage.label(w)
    nlbl = numpy.arange(1, nlbl + 1, 1)
    flvec = []
    depthvec = []
    lenvec = []
    for i in enumerate(nlbl):
        indices = numpy.where(lbls == i[1])
        s = w[indices]
        t = fwhm[indices]
        lenvec.append(len(s))
        depthvec.append(numpy.max(s))
        flvec.append(numpy.sum(numpy.multiply(t, s)))
    lenvec = numpy.array(lenvec)
    depthvec = numpy.array(depthvec)
    flvec = numpy.array(flvec)
    ast = depthvec / lenvec
    lensum = numpy.sum(lenvec)  # neos
    astsum = numpy.sum(ast)
    ast /= astsum
    depthsum = numpy.sum(depthvec)
    flsum = numpy.sum(flvec)
    flvec /= flsum
    depthvec /= depthsum
    alles = (ast + flvec + depthvec) / 3.0
    allessum = numpy.sum(alles)
    alles /= allessum
    for j in enumerate(nlbl):
        ind = numpy.where(lbls == j[1])
        w[ind] = w[ind] * alles[j[0]]
        ww[ind] = ww[ind] * alles[j[0]]
    return w, ww, astsum, depthsum, flsum, allessum


# check features

def scrut_weigh3(rm_abs, rm_rel, wav, vnir_thr, swir_thr):
    r_abs = copy.deepcopy(rm_abs)
    r_rel = copy.deepcopy(rm_rel)
    r_abs_mod = copy.deepcopy(rm_abs)
    fwhm = wav - numpy.roll(wav, 1)
    fwhm[0] = fwhm[1]
    vnirmax = 0
    swirmax = 0
    if numpy.sum(r_rel) == 0:
        return r_rel, r_rel, vnirmax, swirmax
    lbls, nlbl = ndimage.label(r_abs)
    nlbl = numpy.arange(1, nlbl + 1, 1)
    for i in enumerate(nlbl):
        indices = numpy.where(lbls == i[1])
        s = r_abs[indices]
        t = wav[indices]
        if numpy.min(t) < 1000:
            threshold = vnir_thr * 10000
        if numpy.min(t) >= 1000:
            threshold = swir_thr * 10000
        maxi = numpy.max(s)
        wasserband1 = numpy.where((t >= 1290) & (t <= 1450))[0]
        wasserband2 = numpy.where((t >= 1750) & (t <= 2010))[0]
        if len(wasserband1) != 0:
            r_abs_mod[indices] = numpy.zeros([len(indices)])
            r_rel[indices] = numpy.ones([len(indices)])
        if len(wasserband2) != 0:
            r_abs_mod[indices] = numpy.zeros([len(indices)])
            r_rel[indices] = numpy.ones([len(indices)])
        if maxi <= threshold:
            r_abs_mod[indices] = numpy.zeros([len(indices)])
            r_rel[indices] = numpy.ones([len(indices)])
    r_rel = numpy.ones([len(r_rel)]) - r_rel
    if numpy.max(wav) <= 1250:
        r_abs_mod_vnir = numpy.where(wav < 1250)[0]
        vnirmax = numpy.max(r_abs_mod[r_abs_mod_vnir])
        vnirargmax = numpy.argmax(r_abs_mod[r_abs_mod_vnir])
        posvnirmax = wav[r_abs_mod_vnir][vnirargmax]
        posswirmax = 0
        swirargmax = 0
        swirmax = 0
    if numpy.max(wav) >= 1250:
        r_abs_mod_vnir = numpy.where(wav < 1250)[0]
        r_abs_mod_swir = numpy.where(wav >= 1250)[0]
        vnirmax = numpy.max(r_abs_mod[r_abs_mod_vnir])
        vnirargmax = numpy.argmax(r_abs_mod[r_abs_mod_vnir])
        swirmax = numpy.max(r_abs_mod[r_abs_mod_swir])
        swirargmax = numpy.argmax(r_abs_mod[r_abs_mod_swir])
        posvnirmax = wav[r_abs_mod_vnir][vnirargmax]
        posswirmax = wav[r_abs_mod_swir][swirargmax]
    return r_abs_mod, r_rel, vnirmax, swirmax, posvnirmax, posswirmax

def corr(libdat_rel_weighted, w_rel_scale):
    sz = numpy.corrcoef(numpy.concatenate((libdat_rel_weighted, w_rel_scale[numpy.newaxis, :])))
    correlate = sz[-1, :-1]
    correlate = numpy.nan_to_num(correlate)
    return correlate


def unmixxx(crmlib, spec, corrcoeffs, thresh=0.5):
    dff = numpy.zeros_like(corrcoeffs)
    dff = dff * -9999
    index = numpy.where(corrcoeffs >= thresh)
    index = index[0]
    dff[index], residuum = optimize.nnls(crmlib[index, :].T, spec)
    return dff, residuum


##########End Feature Weights
#############
#####
# input wavelength and spectrum in new resolution and abs weighted spectrum

def lo_hull(wv, spc, absolute, thr=0.0001):
    msk = numpy.where(absolute <= thr, 0, 1)
    absolute *= msk
    lbls, nlbl = ndimage.label(absolute)
    nlbl = numpy.arange(1, nlbl + 1, 1)
    dada = []
    wb = []
    dada.append(wv[0])
    wb.append(spc[0])
    for i in enumerate(nlbl):
        indices = numpy.where(lbls == i[1])
        s = absolute[indices]
        t = wv[indices]
        spp = spc[indices]
        sd = numpy.argmax(s)
        dada.append(t[sd])
        wb.append(spp[sd])
    dada.append(wv[-1])
    wb.append(spc[-1])
    dadan = numpy.asarray(dada)
    wbn = numpy.asarray(wb)
    hull = numpy.interp(wv, dadan, wbn)
    minn = spc - hull
    negmsk = numpy.where(minn < 0, 1, 0)
    minnn = minn * negmsk
    minnn = numpy.abs(minnn)
    lbls, nlbl = ndimage.label(minnn)
    nlbl = numpy.arange(1, nlbl + 1, 1)
    for i in enumerate(nlbl):
        indices = numpy.where(lbls == i[1])
        s = minnn[indices]
        t = wv[indices]
        spp = spc[indices]
        sd = numpy.argmax(s)
        dada.append(t[sd])
        wb.append(spp[sd])
    hullx = numpy.asarray(dada)
    hully = numpy.asarray(wb)
    argh1 = numpy.argsort(hullx)
    hullneox = hullx[argh1]
    hullneoy = hully[argh1]
    hulllfin = numpy.interp(wv, hullneox, hullneoy)
    feinalpos = numpy.nan_to_num(spc - hulllfin)  # absolute removal
    norms = numpy.nan_to_num(hulllfin / spc)  # relative removal
    numpy.place(norms, norms > 1, 1)
    numpy.place(norms, norms < 0, 0)
    numpy.place(feinalpos, feinalpos < 0, 0)
    relative = norms
    return wv, spc, hull, hulllfin, feinalpos, relative


def treat_library_cvx(wv, data, neowave, vnir_thr=0.01, swir_thr=0.02):
    arr, nwv = interpolate_generic1nmlib_nwave(wv, data, neowave, flag=0)
    cvxabs = numpy.zeros_like(arr)
    cvxrel = numpy.zeros_like(arr)
    cvxhull = numpy.zeros_like(arr)
    w_rel_chm_scale = numpy.zeros_like(arr)
    w_rel_scale = numpy.zeros_like(arr)
    cvxrel_mod = numpy.zeros_like(arr)
    cvxabs_mod = numpy.zeros_like(arr)
    posvnirmax = numpy.zeros((arr.shape[0]))
    posswirmax = numpy.zeros((arr.shape[0]))
    swirmax = numpy.zeros((arr.shape[0]))
    vnirmax = numpy.zeros((arr.shape[0]))
    for j in numpy.arange(0, arr.shape[0], 1):
        try:
            cvxabs[j, :], cvxrel[j, :], cvxhull[j, :] = cvx_uhull2(arr[j, :], nwv, cont_switch=1)
            cvxabs_mod[j, :], cvxrel_mod[j, :], vnirmax[j], swirmax, posvnirmax[j], posswirmax[j] = scrut_weigh3(
                cvxabs[j, :], cvxrel[j, :], nwv, vnir_thr, swir_thr)
            w_rel_scale[j, :], w_rel_chm_scale[j, :], a, b, c, d = weighting_lib2(cvxrel_mod[j, :], nwv)
        except Exception:
            #print('treat_library_cvx-->E')
            cvxabs_mod[j, :], cvxrel_mod[j, :], vnirmax[j], swirmax, posvnirmax[j], posswirmax[j] = numpy.zeros_like(
                arr[j, :]), numpy.ones_like(arr[j, :]), 0, 0, 0, 0
            continue
    return cvxabs_mod, cvxrel_mod, w_rel_scale, w_rel_chm_scale, vnirmax, swirmax


def treat_library_cvx_full_range(wv, data, neowave, vnir_thr=0.00, swir_thr=0.00):
    print('...calculating values for library endmembers...')
    arr, nwv = interpolate_generic1nmlib_nwave(wv, data, neowave, flag=0)
    # return arr,nwv
    cvxabs = numpy.zeros_like(arr)
    cvxrel = numpy.zeros_like(arr)
    cvxhull = numpy.zeros_like(arr)
    w_rel_chm_scale = numpy.zeros_like(arr)
    w_rel_scale = numpy.zeros_like(arr)
    cvxrel_mod = numpy.zeros_like(arr)
    cvxabs_mod = numpy.zeros_like(arr)
    posvnirmax = numpy.zeros((arr.shape[0]))
    posswirmax = numpy.zeros((arr.shape[0]))
    swirmax = numpy.zeros((arr.shape[0]))
    vnirmax = numpy.zeros((arr.shape[0]))
    for j in numpy.arange(0, arr.shape[0], 1):
        try:
            cvxabs[j, :], cvxrel[j, :], cvxhull[j, :] = cvx_hull(arr[j, :], nwv, cont_switch=1)
            cvxabs_mod[j, :], cvxrel_mod[j, :], vnirmax[j], swirmax, posvnirmax[j], posswirmax[j] = scrut_weigh3(
                cvxabs[j, :], cvxrel[j, :], nwv, vnir_thr, swir_thr)
            w_rel_scale[j, :], w_rel_chm_scale[j, :], a, b, c, d = weighting_lib2(cvxrel_mod[j, :], nwv)
        except Exception:
            #print('treat_library_cvx_full_range-->E')
            cvxabs[j, :], cvxrel[j, :], cvxhull[j, :] = numpy.zeros_like(arr[j, :]), numpy.ones_like(arr[j, :]), arr[j,
                                                                                                                 :]  # Please mind the colinearity!
    return cvxabs_mod, cvxrel_mod, w_rel_scale, w_rel_chm_scale, vnirmax, swirmax


# hull calculation Only!


def treat_library_cvx_full_range_lo(wv, data, neowave, vnir_thr=0.00, swir_thr=0.00):
    arr, nwv = interpolate_generic1nmlib_nwave(wv, data, neowave, flag=0)
    # return arr,nwv
    cvxabs = numpy.zeros_like(arr)
    cvxabsa = numpy.zeros_like(arr)  #
    cvxabsb = numpy.zeros_like(arr)  #
    cvxrel = numpy.zeros_like(arr)
    cvxhull = numpy.zeros_like(arr)
    cvxhullb = numpy.zeros_like(arr)  #
    cvxhullc = numpy.zeros_like(arr)  #
    w_rel_chm_scale = numpy.zeros_like(arr)
    w_rel_scale = numpy.zeros_like(arr)
    cvxrel_mod = numpy.zeros_like(arr)
    cvxabs_mod = numpy.zeros_like(arr)
    posvnirmax = numpy.zeros((arr.shape[0]))
    posswirmax = numpy.zeros((arr.shape[0]))
    swirmax = numpy.zeros((arr.shape[0]))
    vnirmax = numpy.zeros((arr.shape[0]))
    cvx_poshull = numpy.zeros_like(arr)
    for j in numpy.arange(0, arr.shape[0], 1):
        try:
            cvxabs[j, :], cvxrel[j, :], cvxhull[j, :] = cvx_hull(arr[j, :], nwv, cont_switch=1)
            cvxabs[j, :], cvxrel_mod[j, :], vnirmax[j], swirmax, posvnirmax[j], posswirmax[j] = scrut_weigh3(
                cvxabs[j, :], cvxrel[j, :], nwv, vnir_thr, swir_thr)  # cvxabsb
            w_rel_scale[j, :], w_rel_chm_scale[j, :], a, b, c, d = weighting_lib2(cvxrel_mod[j, :], nwv)
            wv1, spc1, hull1, hulllfin1, feinalpos1, relative1 = lo_hull(nwv, arr[j, :], w_rel_chm_scale[j,
                                                                                         :])  #####################NEU Reflectance Peaks
            # cvxhullb[j,:]=feinalpos1#
            # cvxhullc[j,:]=hulllfin1#
            cvxabs[j, :], cvxrel_mod[j, :], vnirmax[j], swirmax, posvnirmax[j], posswirmax[j] = scrut_weigh3(feinalpos1,
                                                                                                             relative1,
                                                                                                             nwv,
                                                                                                             vnir_thr,
                                                                                                             swir_thr)  #####################NEU Reflectance Peaks
            w_rel_scale[j, :], w_rel_chm_scale[j, :], a, b, c, d = weighting_lib2(cvxrel_mod[j, :],
                                                                                  nwv)  #####################NEU Reflectance Peaks
        except Exception:
            print('treat_library_cvx_full_range_lo-->E')
            cvxabs[j, :], cvxrel[j, :], cvxhull[j, :] = numpy.zeros_like(arr[j, :]), numpy.ones_like(arr[j, :]), arr[j,
                                                                                                                 :]  # Please mind the colinearity!
    return cvxabs_mod, cvxrel_mod, w_rel_scale, w_rel_chm_scale, vnirmax, swirmax  # ,cvxhull,cvxabsa,cvxabsb,cvxhullb,cvxhullc


#########
########Fitting Routines
###########


def fitting_cvx(wfrom, wto, data, libdat_rel_weighted, libdat_rel_chm_weighted, libdat_abs, vnir_thr=0.01,
                swir_thr=0.02, lib_flag=0, mix_minerals=6, fit_threshold=0.5):
    dshape2 = data.shape
    data = data.reshape(dshape2[0], dshape2[1] * dshape2[2])
    dshape = data.shape
    lshape = libdat_rel_weighted.shape
    correlat = numpy.zeros([lshape[0], dshape[1]])
    vnirdepthmat = numpy.zeros([dshape[1]])
    swirdepthmat = numpy.zeros([dshape[1]])
    vnirposmat = numpy.zeros([dshape[1]])
    swirposmat = numpy.zeros([dshape[1]])
    leastsquares = numpy.ones([lshape[0], dshape[1]]) * 0  # *-999
    bvlss = numpy.ones([lshape[0], dshape[1]]) * 0  # *-999
    bvlserr = numpy.ones([dshape[1]])  # *-999
    lsqerr = numpy.ones([dshape[1]])  # *-999
    astsum = numpy.zeros([dshape[1]])
    depthsum = numpy.zeros([dshape[1]])
    flsum = numpy.zeros([dshape[1]])
    allessum = numpy.zeros([dshape[1]])
    for j in numpy.arange(0, dshape[1], 1):
        output = interpolate_1nm_spectrum(wto, wfrom, data[:, j], flag=None)
        if numpy.sum(output == 0):
            rm_abs_dat = output
            rm_rel_dat = output
            hull_dat = output
            correlat[:, j] = numpy.zeros([lshape[0]])
            vnirdepthmat[j] = -1
            swirdepthmat[j] = -1
            vnirposmat[j] = -1
            swirposmat[j] = -1
            astsum[j] = -1
            depthsum[j] = -1
            flsum[j] = -1
            allessum[j] = -1
        else:
            try:
                rm_abs_dat, rm_rel_dat, hull_dat = cvx_uhull2(output, wto, cont_switch=1)
                absolutee, relativee, vnirdepthmat[j], swirdepthmat[j], vnirposmat[j], swirposmat[j] = scrut_weigh3(
                    rm_abs_dat, rm_rel_dat, wto, vnir_thr, swir_thr)
                w_rel_scale, w_rel_chm_scale, a, b, c, d = weighting_lib2(relativee, wto)
                astsum[j] = a
                depthsum[j] = b
                flsum[j] = c
                allessum[j] = d
                correlat[:, j] = corr(libdat_rel_weighted, w_rel_scale)
                numpy.nan_to_num(correlat[:, j])
                correlat[:, j][~numpy.isfinite(correlat[:, j])] = 0
                numpy.place(correlat[:, j], correlat[:, j] <= 0, 0)
            except Exception:
                pass
            try:
                bvlss[:, j], bvlserr[j] = unmixxx(libdat_abs, absolutee, correlat[:, j], thresh=0.5)
            except Exception:
                bvlserr[j] = 9999
    return correlat, bvlss, bvlserr, vnirposmat, vnirdepthmat, swirposmat, swirdepthmat, astsum, depthsum, flsum, allessum


def fitting_cvx_fullrange(wfrom, wto, data, libdat_rel_weighted, libdat_rel_chm_weighted, libdat_abs, vnir_thr=0.00,
                          swir_thr=0.00, lib_flag=0, mix_minerals=6, fit_threshold=0.5):
    print('...feature fitting and bvls...')
    dshape2 = data.shape
    data = data.reshape(dshape2[0], dshape2[1] * dshape2[2])
    dshape = data.shape
    lshape = libdat_rel_weighted.shape
    correlat = numpy.zeros([lshape[0], dshape[1]])
    vnirdepthmat = numpy.zeros([dshape[1]])
    swirdepthmat = numpy.zeros([dshape[1]])
    vnirposmat = numpy.zeros([dshape[1]])
    swirposmat = numpy.zeros([dshape[1]])
    leastsquares = numpy.ones([lshape[0], dshape[1]]) * 0  # *-999
    bvlss = numpy.ones([lshape[0], dshape[1]]) * 0  # *-999
    bvlserr = numpy.ones([dshape[1]])  # *-999
    lsqerr = numpy.ones([dshape[1]])  # *-999
    astsum = numpy.zeros([dshape[1]])
    depthsum = numpy.zeros([dshape[1]])
    flsum = numpy.zeros([dshape[1]])
    allessum = numpy.zeros([dshape[1]])
    for j in numpy.arange(0, dshape[1], 1):
        output = interpolate_1nm_spectrum(wto, wfrom, data[:, j], flag=None)
        if numpy.sum(output == 0):
            rm_abs_dat = output
            rm_rel_dat = output
            hull_dat = output
            correlat[:, j] = numpy.zeros([lshape[0]])
            vnirdepthmat[j] = -1
            swirdepthmat[j] = -1
            vnirposmat[j] = -1
            swirposmat[j] = -1
            astsum[j] = -1
            depthsum[j] = -1
            flsum[j] = -1
            allessum[j] = -1
        else:
            try:
                rm_abs_dat, rm_rel_dat, hull_dat = cvx_hull(output, wto, cont_switch=1)
                absolutee, relativee, vnirdepthmat[j], swirdepthmat[j], vnirposmat[j], swirposmat[j] = scrut_weigh3(
                    rm_abs_dat, rm_rel_dat, wto, vnir_thr, swir_thr)
                w_rel_scale, w_rel_chm_scale, a, b, c, d = weighting_lib2(relativee, wto)
                astsum[j] = a
                depthsum[j] = b
                flsum[j] = c
                allessum[j] = d
                correlat[:, j] = corr(libdat_rel_weighted, w_rel_scale)
                numpy.nan_to_num(correlat[:, j])
                correlat[:, j][~numpy.isfinite(correlat[:, j])] = 0
                numpy.place(correlat[:, j], correlat[:, j] <= 0, 0)
            except Exception:
                pass
            try:
                bvlss[:, j], bvlserr[j] = unmixxx(libdat_abs, absolutee, correlat[:, j], thresh=0.5)
            except Exception:
                bvlserr[j] = 9999
    return correlat, bvlss, bvlserr, vnirposmat, vnirdepthmat, swirposmat, swirdepthmat, astsum, depthsum, flsum, allessum


def fitting_cvx_fullrange_lo(wfrom, wto, data, libdat_rel_weighted, libdat_rel_chm_weighted, libdat_abs, vnir_thr,
                             swir_thr, lib_flag, mix_minerals, fit_threshold):
    dshape2 = data.shape
    data = data.reshape(dshape2[0], dshape2[1] * dshape2[2])
    dshape = data.shape
    lshape = libdat_rel_weighted.shape
    correlat = numpy.zeros([lshape[0], dshape[1]])
    vnirdepthmat = numpy.zeros([dshape[1]])
    swirdepthmat = numpy.zeros([dshape[1]])
    vnirposmat = numpy.zeros([dshape[1]])
    swirposmat = numpy.zeros([dshape[1]])
    leastsquares = numpy.ones([lshape[0], dshape[1]]) * 0  # *-999
    bvlss = numpy.ones([lshape[0], dshape[1]]) * 0  # *-999
    bvlserr = numpy.ones([dshape[1]])  # *-999
    lsqerr = numpy.ones([dshape[1]])  # *-999
    astsum = numpy.zeros([dshape[1]])
    depthsum = numpy.zeros([dshape[1]])
    flsum = numpy.zeros([dshape[1]])
    allessum = numpy.zeros([dshape[1]])
    for j in numpy.arange(0, dshape[1], 1):
        output = interpolate_1nm_spectrum(wto, wfrom, data[:, j], flag=None)
        if numpy.sum(output == 0):
            rm_abs_dat = output
            rm_rel_dat = output
            hull_dat = output
            correlat[:, j] = numpy.zeros([lshape[0]])
            vnirdepthmat[j] = -1
            swirdepthmat[j] = -1
            vnirposmat[j] = -1
            swirposmat[j] = -1
            astsum[j] = -1
            depthsum[j] = -1
            flsum[j] = -1
            allessum[j] = -1
        else:
            try:
                rm_abs_dat, rm_rel_dat, hull_dat = cvx_hull(output, wto, cont_switch=1)
                absolutee, relativee, vnirdepthmat[j], swirdepthmat[j], vnirposmat[j], swirposmat[j] = scrut_weigh3(
                    rm_abs_dat, rm_rel_dat, wto, vnir_thr, swir_thr)
                w_rel_scale, w_rel_chm_scale, a, b, c, d = weighting_lib2(relativee, wto)
            except Exception:
                bvlserr[j] = 9999
                rm_abs_dat = output
                rm_rel_dat = output
                hull_dat = output
                correlat[:, j] = numpy.zeros([lshape[0]])
                vnirdepthmat[j] = -1
                swirdepthmat[j] = -1
                vnirposmat[j] = -1
                swirposmat[j] = -1
                astsum[j] = -1
                depthsum[j] = -1
                flsum[j] = -1
                allessum[j] = -1
                pass
            try:
                wv1_bil, spc1_bil, hull1_bil, hulllfin1_bil, feinalpos1_bil, relative1_bil = lo_hull(wto, output,
                                                                                                     w_rel_chm_scale)  #####################NEU Reflectance Peaks#
                cvxabs_mod_bil, cvxrel_mod_bil, vnirmax_bil, swirmax_bil, posvnirmax_bil, posswirmax_bil = scrut_weigh3(
                    feinalpos1_bil, relative1_bil, wto, vnir_thr, swir_thr)  #####################NEU Reflectance Peaks
                w_rel_scale_bil, w_rel_chm_scale_bil, a1, b1, c1, d1 = weighting_lib2(cvxrel_mod_bil,
                                                                                      wto)  #####################NEU Reflectance Peaks
                astsum[j] = a1
                depthsum[j] = b1
                flsum[j] = c1
                allessum[j] = d1
                correlat[:, j] = corr(libdat_rel_weighted, w_rel_scale_bil)
                numpy.nan_to_num(correlat[:, j])
                correlat[:, j][~numpy.isfinite(correlat[:, j])] = 0
                numpy.place(correlat[:, j], correlat[:, j] <= 0, 0)
            except Exception:
                bvlserr[j] = 9999
                rm_abs_dat = output
                rm_rel_dat = output
                hull_dat = output
                correlat[:, j] = numpy.zeros([lshape[0]])
                vnirdepthmat[j] = -1
                swirdepthmat[j] = -1
                vnirposmat[j] = -1
                swirposmat[j] = -1
                astsum[j] = -1
                depthsum[j] = -1
                flsum[j] = -1
                allessum[j] = -1
            try:
                bvlss[:, j], bvlserr[j] = unmixxx(libdat_abs_bil, cvxabs_mod_bil, correlat[:, j], thresh=0.5)
            except Exception:
                bvlserr[j] = 9999
    return correlat, bvlss, bvlserr, vnirposmat, vnirdepthmat, swirposmat, swirdepthmat, astsum, depthsum, flsum, allessum


###
###End Fitting Routines
############

########
###Class color result functions
##########

def writiff(rgb, out):
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(rgb)
    dst_ds = driver.Create(out, h[2], h[1], h[0], gdal.GDT_Byte)
    ka = 1
    while ka <= h[0]:
        hhh = ka - 1
        dst_ds.GetRasterBand(ka).WriteArray(rgb[hhh, :, :])
        ka += 1
    dst_ds = None


def reshreib(data, name, shp):
    print('...writing results to disk...')
    data = data.reshape(shp)
    schreibeBSQ(data, name)
    return None


def reshreib2d(data, name, shp):
    data = data.reshape(shp)
    schreibeBSQsingle(data, name)
    return None


def own_mix_corelation(corelate1, mix_minerals):
    shp = corelate1.shape
    corelate1[~numpy.isfinite(corelate1)] = 0
    # print numpy.max(corelate1)
    # print numpy.min(corelate1)
    ws = numpy.ones([mix_minerals, shp[1]]) * -999
    w_corrcoef = numpy.zeros([mix_minerals, shp[1]])
    for i in numpy.arange(0, shp[1], 1):
        zd = copy.deepcopy(corelate1[:, i])
        for j in numpy.arange(0, mix_minerals, 1):
            index = numpy.where(zd == numpy.max(zd))
            if numpy.max(zd) == 0:
                break
            else:
                if len(index[0]) > 1:
                    ind = index[0][0]
                else:
                    ind = index[0]
                ws[j, i] = ind
                w_corrcoef[j, i] = zd[ind]
                zd[ind] = 0
    return ws, w_corrcoef


def setzus(liste):
    liste = str(liste)
    liste = liste.replace('[', '{')
    liste = liste.replace(']', '}')
    liste = liste.replace('\'', '')
    return liste


def setzusdescript(liste):
    liste = str(liste)
    liste = liste.replace('[', '(')
    liste = liste.replace(']', ')')
    liste = liste.replace(',', ';')
    liste = liste.replace('\'', '')
    return liste


def loadmineral_colors(mintxt):
    with open(mintxt, 'r') as file:
        d = file.readlines()
    namen = []
    B = []
    G = []
    R = []
    index = []
    for i in enumerate(d):
        if i[0] == 0:
            continue
        ah = i[1].strip().split(',')
        # print ah
        namen.append(ah[0])
        R.append(ah[1].strip())
        G.append(ah[2].strip())
        B.append(ah[3].strip())
        index.append(i[0])
    B = numpy.array(B)
    G = numpy.array(G)
    R = numpy.array(R)
    index = numpy.array(index)
    index = numpy.arange(numpy.min(index) - 1, numpy.max(index), 1)
    return namen, index, R, G, B


def schreibefarbfile7(numpyarray, out, classfilename):
    obd = loadmineral_colors(classfilename)
    farbfile = numpy.stack((obd[2], obd[3], obd[4]), axis=-1)
    farbfile = farbfile.astype('uint8')
    sh = numpyarray.shape
    numpyarray = numpyarray.reshape(sh[0] * sh[1])
    farbe = numpy.zeros([sh[0] * sh[1], 3])
    for i in numpy.arange(0, sh[0] * sh[1], 1):
        if numpyarray[i] < 0:
            continue
        # print(numpyarray[i])
        farbe[i, :] = farbfile[int(numpyarray[i]), :]
    farbe = farbe.astype('uint8')
    farbe = farbe.reshape(sh[0], sh[1], 3)
    rgb = farbe
    format = "ENVI"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(rgb)
    dst_ds = driver.Create(out + '_geotiff.tif', h[2], h[1], h[0], gdal.GDT_Byte)
    ka = 1
    while ka <= h[0]:
        hhh = ka - 1
        dst_ds.GetRasterBand(ka).WriteArray(rgb[hhh, :, :])
        ka += 1
    dst_ds = None
    return rgb


##########
################
########################
#############################WRITE cOLORFILE
def schreibeBSQsingle_band_class_best_matchmat(numpyarray, out, classfilename):
    numpy.place(numpyarray, numpyarray < 0, 255)
    numpyarray = numpyarray.astype('uint8')
    format = "ENVI"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(numpyarray)
    dst_ds = driver.Create(out, h[1], h[0], 1, gdal.GDT_Byte)
    dst_ds.GetRasterBand(1).WriteArray(numpyarray)
    dst_ds = None
    unik_vals = numpy.unique(numpyarray)
    classes_numbers = len(unik_vals)
    ####
    obd = loadmineral_colors(classfilename)
    ####
    len_obd = len(obd[1])
    print('Total number of library entries = ', len_obd)
    ###
    print('Number of library endmembers present in the EnGeoMAP classification result = ', classes_numbers)
    ####
    description = []
    class_names = []
    class_lookup = []
    rgb = numpy.array([copy.deepcopy(numpyarray), copy.deepcopy(numpyarray), copy.deepcopy(numpyarray)])
    rgb *= 0
    for i in enumerate(obd[1]):
        if i[1] == 255:
            class_lookup.append('0' + ',' + '0' + ',' + '0')
            class_names.append('No_Fit_Possible')
            description.append('255=No_Fit_Possible')
            numpy.place(rgb[0, :, :], numpyarray[:, :] == 255, 0)
            numpy.place(rgb[1, :, :], numpyarray[:, :] == 255, 0)
            numpy.place(rgb[2, :, :], numpyarray[:, :] == 255, 0)
            break
        numpy.place(rgb[0, :, :], numpyarray[:, :] == i[1], int(obd[2][i[1]]))
        numpy.place(rgb[1, :, :], numpyarray[:, :] == i[1], int(obd[3][i[1]]))
        numpy.place(rgb[2, :, :], numpyarray[:, :] == i[1], int(obd[4][i[1]]))
        class_lookup.append(obd[2][i[1]] + ',' + obd[3][i[1]] + ',' + obd[4][i[1]])
        class_names.append(obd[0][i[1]].strip())
        description.append(str(i[1]) + '=' + obd[0][i[1]].strip())
    orighdr = return_header_list(out + '.hdr')
    description = setzusdescript(description)
    class_names = setzus(class_names)
    class_lookup = setzus(class_lookup)
    class_lookup = 'class lookup = ' + class_lookup + '\n'
    cnum = 'classes =' + str(len_obd) + '\n'
    description = 'description =' + '{' + description + '}' + '\n'
    class_names = 'class names =' + class_names + '\n'
    orighdr[5] = 'file type = ENVI Classification' + '\n'
    orighdr.insert(1, description)
    orighdr.append(cnum)
    orighdr.append(class_lookup)
    orighdr.append(class_names)
    with open(out + '.hdr', 'w') as file:
        file.writelines(orighdr)
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(rgb)
    dst_ds = driver.Create(out + '_geotiff.tif', h[2], h[1], h[0], gdal.GDT_Byte)
    ka = 1
    while ka <= h[0]:
        hhh = ka - 1
        dst_ds.GetRasterBand(ka).WriteArray(rgb[hhh, :, :])
        ka += 1
    dst_ds = None
    return rgb


def geohtiff(rgb, out):
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(rgb)
    dst_ds = driver.Create(out + '_segment_median_geotiff.tif', h[2], h[1], h[0], gdal.GDT_Byte)
    ka = 1
    while ka <= h[0]:
        hhh = ka - 1
        dst_ds.GetRasterBand(ka).WriteArray(rgb[hhh, :, :])
        ka += 1
    dst_ds = None


def own_mix_distance(corelate1, mix_minerals):
    shp = corelate1.shape
    corelate1[~numpy.isfinite(corelate1)] = 0
    ws = numpy.ones([mix_minerals, shp[1]]) * -999
    w_corrcoef = numpy.zeros([mix_minerals, shp[1]])
    for i in numpy.arange(0, shp[1], 1):
        zd = copy.deepcopy(corelate1[:, i])
        for j in numpy.arange(0, mix_minerals, 1):
            index = numpy.where(zd == numpy.min(zd))
            if numpy.min(zd) == 0:
                break
            else:
                if len(index[0]) > 1:
                    ind = index[0][0]
                else:
                    ind = index[0]
                ws[j, i] = ind
                w_corrcoef[j, i] = zd[ind]
                zd[ind] = 0
    return ws, w_corrcoef


def corr_colours(corrmat, colorfile, basename, shape_param, minerals=30, thresh=0.5):
    threshold_applied = copy.deepcopy(corrmat)
    numpy.place(threshold_applied, threshold_applied < thresh, 0)
    indexmat, maxcormat = own_mix_corelation(threshold_applied, minerals)
    indexmat = indexmat.reshape(minerals, shape_param[1], shape_param[2])
    maxcormat = maxcormat.reshape(minerals, shape_param[1], shape_param[2])
    # schreibeBSQ(maxcormat,basename+'_best_matches_')
    # schreibeBSQ(indexmat,basename+'_best_matches_indices')
    rgb = schreibeBSQsingle_band_class_best_matchmat(indexmat[0, :, :], basename + '_result', colorfile)
    indexmedian = signal.medfilt2d(indexmat[0, :, :], kernel_size=3)
    # schreibeBSQsingle(indexmedian,basename+'_median_filtered_best_match_index')
    # Optional median filtered
    # rgbm=schreibeBSQsingle_band_class_best_matchmat(indexmedian,basename+'_median_filtered_result',colorfile)
    # indexmedian2=signal.medfilt2d(indexmat[1,:,:],kernel_size=3)
    return rgb, indexmat  # ,rgbm


def corr_colours_unmix(corrmat, colorfile, basename, shape_param, minerals, thresh=0.00):
    threshold_applied = copy.deepcopy(corrmat)
    numpy.place(threshold_applied, threshold_applied < thresh, 0)
    indexmat, maxcormat = own_mix_corelation(threshold_applied, minerals)
    indexmat = indexmat.reshape(minerals, shape_param[1], shape_param[2])
    maxcormat = maxcormat.reshape(minerals, shape_param[1], shape_param[2])
    rgb = schreibeBSQsingle_band_class_best_matchmat(indexmat[0, :, :], basename + '_highest_abundance_result', colorfile)
    # schreibeBSQ(maxcormat,basename+'_highest_abundance_unmix_')
    # schreibeBSQ(indexmat,basename+'_highest_abundance_unmix_indices')
    indexmedian = signal.medfilt2d(indexmat[0, :, :], kernel_size=3)
    # schreibeBSQsingle(indexmedian,basename+'_median_filtered_best_match_index')
    # Optional median filtered
    # rgbm=schreibeBSQsingle_band_class_best_matchmat(indexmedian,basename+'_median_filtered_highest_abundance',colorfile)
    # indexmedian2=signal.medfilt2d(indexmat[1,:,:],kernel_size=3)
    return rgb, indexmat  # ,rgbm


def corr_colours_dist(corrmat, colorfile, basename, shape_param, minerals):
    threshold_applied = copy.deepcopy(corrmat)
    indexmat, maxcormat = own_mix_distance(threshold_applied, minerals)
    indexmat = indexmat.reshape(minerals, shape_param[1], shape_param[2])
    maxcormat = maxcormat.reshape(minerals, shape_param[1], shape_param[2])
    schreibeBSQ(maxcormat, basename + '_best_matches_')
    schreibeBSQ(indexmat, basename + '_best_matches_indices')
    rgb = schreibeBSQsingle_band_class_best_matchmat(indexmat[0, :, :], basename + '_result', colorfile)
    return rgb, indexmat


#########
#############
# End Corr Result Color Files

######
####File IO


def schreibeBSQ(numpyarray, out):
    format = "ENVI"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(numpyarray)
    dst_ds = driver.Create(out, h[2], h[1], h[0], gdal.GDT_Float32)
    ka = 1
    while ka <= h[0]:
        hhh = ka - 1
        dst_ds.GetRasterBand(ka).WriteArray(numpyarray[hhh, :, :])
        ka += 1
    dst_ds = None


def schreibeBSQ_int(numpyarray, out):
    format = "ENVI"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(numpyarray)
    dst_ds = driver.Create(out, h[2], h[1], h[0], gdal.GDT_Int16)
    ka = 1
    while ka <= h[0]:
        hhh = ka - 1
        dst_ds.GetRasterBand(ka).WriteArray(numpyarray[hhh, :, :])
        ka += 1
    dst_ds = None


def schreibeBSQsingle(numpyarray, out):
    format = "ENVI"
    driver = gdal.GetDriverByName(format)
    h = numpy.shape(numpyarray)
    dst_ds = driver.Create(out, h[1], h[0], 1, gdal.GDT_Float32)
    dst_ds.GetRasterBand(1).WriteArray(numpyarray)
    dst_ds = None


def own_mix_corelation(corelate1, mix_minerals):
    shp = corelate1.shape
    corelate1[~numpy.isfinite(corelate1)] = 0
    ws = numpy.ones([mix_minerals, shp[1]]) * -999
    w_corrcoef = numpy.zeros([mix_minerals, shp[1]])
    for i in numpy.arange(0, shp[1], 1):
        zd = copy.deepcopy(corelate1[:, i])
        for j in numpy.arange(0, mix_minerals, 1):
            index = numpy.where(zd == numpy.max(zd))
            if numpy.max(zd) == 0:
                break
            else:
                if len(index[0]) > 1:
                    ind = index[0][0]
                else:
                    ind = index[0]
                ws[j, i] = ind
                w_corrcoef[j, i] = zd[ind]
                zd[ind] = 0
    return ws, w_corrcoef


def own_mix_corelation2(corelate1, mix_minerals):
    shp = corelate1.shape
    corelate1[~numpy.isfinite(corelate1)] = 0
    ws = numpy.ones([mix_minerals, shp[1]]) * -999
    w_corrcoef = numpy.zeros([mix_minerals, shp[1]])
    for i in numpy.arange(0, shp[1], 1):
        zd = copy.deepcopy(corelate1[:, i])
        for j in numpy.arange(0, mix_minerals, 1):
            index = numpy.where(zd == numpy.max(zd))
            if numpy.max(zd) == 0:
                break
            if numpy.max(zd) == -999:
                break
            else:
                if len(index[0]) > 1:
                    ind = index[0][0]
                else:
                    ind = index[0]
                ws[j, i] = ind
                w_corrcoef[j, i] = zd[ind]
                zd[ind] = 0
    return ws, w_corrcoef


####
####End File IO
##########
############
############

def listing(path):  # listing all files in this directory, which ends with .hdr
    return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".hdr")]


def rewrite_headers(
        inputbildhdr):  # read orginal header and read map info and crs, create a new list, append map info and crs into empty list (L[]), write L into all hdr files
    pf = inputbildhdr.rfind('/')
    pfad = inputbildhdr[:pf]
    liste = listing(pfad)
    inputs = read_hdr_flt(inputbildhdr)
    L = []
    try:
        mapinfo = inputs.map_info
        mapinfo = 'map info={' + mapinfo + '}\n'
        L.append(mapinfo)
    except(AttributeError):
        print('No coordinate info was found in the input image data -> No coordinate info will be transferred to the classification results header files.')
        return -1
    try:
        crs = inputs.coordinate_system_string
        crs = 'coordinate system string={' + crs + '}\n'
        L.append(crs)
    except(AttributeError):
        print('No CRS Info was found.')
    for j in enumerate(liste):
        if j[1] == inputbildhdr:
            continue
        open(j[1], 'a').writelines(L)
    return None
