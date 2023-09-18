# -*- coding: utf-8 -*-
'''
SAIL.py executes the SAIL model

References:
Verhoef W., Xiao Q., Jia L., & Su Z. (2007):
Unified optical-thermal four-stream radiative transfer theory for homogeneous vegetation canopies.
IEEE Transactions on Geoscience and Remote Sensing, 45, 1808-1822. Article.

Verhoef W., & Bach H. (2003), Simulation of hyperspectral and directional radiance images using coupled biophysical
and atmospheric radiative transfer models. Remote Sensing of Environment, 87, 23-41. Article.

Verhoef W. (1984), Light scattering by leaf layers with application to canopy reflectance modeling: the SAIL model.
Remote Sensing of Environment, 16, 125-141. Article.
'''

from lmuvegetationapps.Resources.PROSAIL.dataSpec import *
from lmuvegetationapps.Resources.PROSAIL.SAILdata import *
import numpy as np

class Sail:

    def __init__(self, tts, tto, psi):

        self.tts = tts
        self.tto = tto
        self.psi = psi

        # Conversions are done in the __init__ to save time (needed as parameters for the complete set of paras)
        self.sintts = np.sin(tts)
        self.sintto = np.sin(tto)
        self.costts = np.cos(tts)
        self.costto = np.cos(tto)
        self.cospsi = np.cos(psi)

    def pro4sail(self, rho, tau, LIDF, TypeLIDF, LAI, hspot, psoil, soil, understory=None, skyl=None,
                 inform_trans=None):

        if inform_trans == 'tto':
            self.tts = self.tto
            self.sintts = self.costto
            self.costts = self.costto

        LAI = LAI[:, np.newaxis]  # expand LAI-array to 2D
        costts_costto = self.costts * self.costto
        tantts = np.tan(self.tts)
        tantto = np.tan(self.tto)
        dso = np.sqrt(tantts ** 2 + tantto ** 2 - 2 * tantts * tantto * self.cospsi)

        # Soil Reflectance Properties
        if type(understory) is np.ndarray:
            soil = understory
        elif not isinstance(soil, np.ndarray):  # "soil" is not supplied as np.array, but is "None" instead
            soil = np.outer(psoil, Rsoil1) + np.outer((1-psoil), Rsoil2)  # np.outer = outer product (vectorized)

        # Generate Leaf Angle Distribution From Average Leaf Angle (ellipsoidal) or (a, b) parameters
        lidf = self.lidf_calc(LIDF, TypeLIDF)

        # Weighted Sums of LIDF
        litab = np.concatenate((np.arange(5, 85, 10), np.arange(81, 91, 2)), axis=0) 
        # litab -> 5, 15, 25, 35, 45, ... , 75, 81, 83, ... 89
        litab = np.radians(litab)

        chi_s, chi_o, frho, ftau = self.volscatt(litab)

        # Extinction coefficients
        ksli = chi_s / self.costts[:, np.newaxis]
        koli = chi_o / self.costto[:, np.newaxis]

        # Area scattering coefficient fractions
        sobli = frho * np.pi / costts_costto[:, np.newaxis]
        sofli = ftau * np.pi / costts_costto[:, np.newaxis]
        bfli = np.cos(litab) ** 2

        # Angular Differences
        ks = np.sum(ksli * lidf, axis=1)[:, np.newaxis]
        ko = np.sum(koli * lidf, axis=1)[:, np.newaxis]
        bf = np.sum(bfli[np.newaxis, :] * lidf, axis=1)[:, np.newaxis]
        sob = np.sum(sobli * lidf, axis=1)[:, np.newaxis]
        sof = np.sum(sofli * lidf, axis=1)[:, np.newaxis]

        # Geometric factors to be used later with reflectance and transmission
        sdb = 0.5 * (ks + bf)
        sdf = 0.5 * (ks - bf)
        dob = 0.5 * (ko + bf)
        dof = 0.5 * (ko - bf)
        ddb = 0.5 * (1 + bf)
        ddf = 0.5 * (1 - bf)

        # Refl and Transm kick in
        sigb = ddb * rho + ddf * tau
        sigf = ddf * rho + ddb * tau
        att = 1.0 - sigf
        m2 = (att + sigb) * (att - sigb)
        m2[m2 < 0] = 0.0
        m = np.sqrt(m2)

        sb = sdb*rho + sdf*tau
        sf = sdf*rho + sdb*tau
        vb = dob*rho + dof*tau
        vf = dof*rho + dob*tau
        w = sob*rho + sof*tau

        # Include LAI (make sure, LAI is > 0!)
        e1 = np.exp(-m * LAI)
        e2 = e1 ** 2
        rinf = (att - m) / sigb
        rinf2 = rinf ** 2
        re = rinf * e1
        denom = 1.0 - rinf2 * e2

        J1ks, tss = self.jfunc1(ks, m, LAI)
        J2ks = self.jfunc2(ks, m, LAI)
        J1ko, too = self.jfunc1(ko, m, LAI)
        J2ko = self.jfunc2(ko, m, LAI)

        Ps = (sf + sb * rinf) * J1ks
        Qs = (sf * rinf + sb) * J2ks
        Pv = (vf + vb * rinf) * J1ko
        Qv = (vf * rinf + vb) * J2ko

        rdd = rinf * (1.0 - e2) / denom
        tdd = (1.0 - rinf2) * e1 / denom
        tsd = (Ps - re * Qs) / denom
        # rsd = (Qs - re*Ps)/denom
        tdo = (Pv - re * Qv) / denom
        rdo = (Qv - re * Pv) / denom

        # tss = np.exp(-ks * LAI)
        # too = np.exp(-ko * LAI)
        z = self.jfunc2(ks, ko, LAI)
        g1 = (z - J1ks * too) / (ko + m)
        g2 = (z - J1ko * tss) / (ks + m)

        Tv1 = (vf * rinf + vb) * g1
        Tv2 = (vf + vb * rinf) * g2
        T1 = Tv1 * (sf + sb * rinf)
        T2 = Tv2 * (sf * rinf + sb)
        T3 = (rdo * Qs + tdo * Ps) * rinf

        # Multiple Scattering contribution to BRDF of canopy
        rsod = (T1 + T2 - T3) / (1.0 - rinf2)

        # Hotspot-effect
        alf = np.where(hspot > 0, ((dso / hspot) * 2.0) / (ks + ko).flatten(), 200)[:, np.newaxis]
        alf[alf > 200] = 200

        fhot = LAI * np.sqrt(ko * ks)
        fint = (1 - np.exp(-alf)) * 0.05
        i19 = np.arange(19)
        x2 = -np.log(1.0 - (i19 + 1) * fint) / alf
        x2[:, 18] = np.ones(x2.shape[0])  # last element in x2 is 1.0
        y2 = -(ko + ks) * LAI * x2 + fhot * (1.0 - np.exp(-alf * x2)) / alf
        f2 = np.exp(y2)

        x1 = np.pad(x2, ((0, 0), (1, 0)), mode='constant')[:, :-1]  # Shifts array by one and fills with constant = 0
        y1 = np.pad(y2, ((0, 0), (1, 0)), mode='constant')[:, :-1]  # -"-
        f1 = np.pad(f2, ((0, 0), (1, 0)), mode='constant', constant_values=1)[:, :-1]  # -"- with constant = 1
        sumint = np.sum((f2 - f1) * (x2 - x1) / (y2 - y1), axis=1)

        tsstoo = np.where(alf == 0, tss, f2[:, -1, np.newaxis])
        sumint = np.where(alf == 0, (1.0 - tss) / (ks * LAI), sumint[:, np.newaxis])

        # Bidirectional reflectance
        rsos = w * LAI * sumint  # Single scattering contribution
        dn = 1.0 - soil * rdd    # Soil interaction
        tdd_dn = tdd / dn
        rdot = rdo + soil * (tdo + too) * tdd_dn  # hemispherical-directional reflectance factor in viewing direction
        rsodt = rsod + ((tss + tsd) * tdo + (tsd + tss * soil * rdd) * too) * soil / dn
        rsost = rsos + tsstoo * soil
        rsot = rsost + rsodt  # rsot: bi-directional reflectance factor

        # Direct/diffuse light
        sin_90tts = np.sin(np.pi / 2 - self.tts)

        if not skyl:
            skyl = 0.847 - 1.61 * sin_90tts + 1.04 * sin_90tts ** 2
        # skyl = 0.1
        if inform_trans:
            PARdiro = (1.0 - skyl)
            PARdiro = PARdiro[:, np.newaxis]
            PARdifo = skyl[:, np.newaxis]
        else:
            PARdiro = np.outer((1.0 - skyl), Es)
            PARdifo = np.outer(skyl, Ed)

        resv = (rdot * PARdifo + rsot * PARdiro) / (PARdiro + PARdifo)

        return resv

    # Calculates the Leaf Angle Distribution Function Value (freq)
    def lidf_calc(self, LIDF, TypeLIDF):

        if TypeLIDF[0] == 1:  # Beta-Distribution, all LUT-members need to have same TypeLIDF!
            freq = beta_dict[LIDF.astype(np.int), :]  # look up frequencies for beta-distribution

        else:  # Ellipsoidal distribution
            freq = self.campbell(LIDF)

        return freq

    # Calculates the Leaf Angle Distribution Function value (freq) Ellipsoidal distribution function from ALIA
    def campbell(self, ALIA):

        n = 13
        excent = np.exp(-1.6184e-5 * ALIA ** 3 + 2.1145e-3 * ALIA ** 2 - 1.2390e-1 * ALIA + 3.2491)
        freq = np.zeros(shape=(ALIA.shape[0], n))

        x1 = excent[:, np.newaxis] / np.sqrt(1.0 + np.outer((excent ** 2), tan_tl1))  # Shape: ns, 13
        x12 = x1 ** 2
        x2 = excent[:, np.newaxis] / np.sqrt(1.0 + np.outer((excent ** 2), tan_tl2))
        x22 = x2 ** 2
        alpha = excent / np.sqrt(np.abs(1 - excent ** 2))
        alpha2 = (alpha ** 2)[:, np.newaxis]

        alpx1 = np.sqrt(alpha2 + x12)
        alpx2 = np.sqrt(alpha2 + x22)
        dump = x1 * alpx1 + alpha2 * np.log(x1 + alpx1)

        almx1 = np.sqrt(alpha2 - x12)
        almx2 = np.sqrt(alpha2 - x22)
        dumm = x1 * almx1 + alpha2 * np.arcsin(x1 / alpha[:, np.newaxis])

        freq[excent > 1.0, :] = np.abs(dump - (x2 * alpx2 + alpha2 * np.log(x2 + alpx2)))[excent > 1.0, :]
        freq[excent < 1.0, :] = np.abs(dumm - (x2 * almx2 + alpha2 *
                                               np.arcsin(x2 / alpha[:, np.newaxis])))[excent < 1.0, :]
        freq[excent == 1.0, :] = np.abs(cos_tl1 - cos_tl2)

        return freq / freq.sum(axis=1)[:, np.newaxis]  # Normalize

    def volscatt(self, ttl):

        costtl = np.cos(ttl)
        sinttl = np.sin(ttl)
        cs = np.outer(self.costts, costtl)
        co = np.outer(self.costto, costtl)
        ss = np.outer(self.sintts, sinttl)
        so = np.outer(self.sintto, sinttl)

        cosbts = np.where(np.abs(ss) > 1e-6, -cs/ss, 5.0)
        cosbto = np.where(np.abs(so) > 1e-6, -co/so, 5.0)
        bts = np.where(np.abs(cosbts) < 1, np.arccos(cosbts), np.pi)
        ds = np.where(np.abs(cosbts) < 1, ss, cs)

        chi_s = 2.0 / np.pi*((bts - np.pi*0.5)*cs + np.sin(bts)*ss)

        bto = np.where(np.abs(cosbto) < 1,
                       np.arccos(cosbto),
                       np.where(self.tto[:, np.newaxis] < np.pi * 0.5, np.pi, 0.0))
        doo = np.where(np.abs(cosbto) < 1, so, np.where(self.tto[:, np.newaxis] < np.pi * 0.5, co, -co))

        chi_o = 2.0 / np.pi * ((bto - np.pi * 0.5)*co + np.sin(bto) * so)

        btran1 = np.abs(bts - bto)
        btran2 = np.pi - np.abs(bts + bto - np.pi)

        bt1 = np.where(self.psi[:, np.newaxis] < btran1, self.psi[:, np.newaxis], btran1)
        bt2 = np.where(self.psi[:, np.newaxis] < btran1, btran1, np.where(self.psi[:, np.newaxis]
                                                                          <= btran2, self.psi[:, np.newaxis], btran2))
        bt3 = np.where(self.psi[:, np.newaxis] < btran1, btran2, np.where(self.psi[:, np.newaxis]
                                                                          <= btran2, btran2, self.psi[:, np.newaxis]))

        t1 = 2 * cs * co + ss * so * self.cospsi[:, np.newaxis]
        t2 = np.where(bt2 > 0, np.sin(bt2) * (2 * ds * doo + ss * so * np.cos(bt1) * np.cos(bt3)), 0)

        denom = 2.0 * np.pi ** 2
        frho = ((np.pi - bt2) * t1 + t2) / denom
        ftau = (-bt2 * t1 + t2) / denom

        frho[frho < 0] = 0.0
        ftau[ftau < 0] = 0.0

        return chi_s, chi_o, frho, ftau

    def jfunc1(self, k_para, l_para, t):  # J1 function with avoidance of singularity problem
        kl = k_para - l_para
        Del = kl * t
        minlt = np.exp(-l_para * t)
        minkt = np.exp(-k_para * t)
        Jout = np.where(np.abs(Del) > 1e-3,
                        (minlt - minkt) / kl,
                        0.5 * t * (minkt + minlt) * (1.0 - Del * Del / 12))
        return Jout, minkt

    def jfunc2(self, k_para, l_para, t):
        kt = k_para + l_para
        Jout = (1.0 - np.exp(-kt * t)) / kt
        return Jout
