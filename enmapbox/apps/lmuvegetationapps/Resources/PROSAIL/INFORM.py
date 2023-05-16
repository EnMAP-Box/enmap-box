""" % INFORM_PROSPECT45D - The INvertible FOrest Reflectance Model coupled with
Prospect 4 or 5 or 5b or D
# %
[r_forest,r_understorey,r_c_inf,r_leaf,t_leaf,t_s,t_o,co,C,G]= ...
   inform_prospect45(wl,PARA_PRO,PARA_INFORM,t_o,t_s,psi,skyl,r_soil,hot)
# %
INFORM (Atzberger, 2000; Schlerf&Atzberger, 2005) simulates the bi-
directional reflectance of forest stands between 400 and 2500 nm. INFORM
is essentially an innovative combination of FLIM (Rosema et al., 1992),
SAIL (Verhoef, 1984), and PROSPECT (Jacquemoud & Baret, 1990) or
LIBERTY (Dawson et al., 1998).
# %
INPUT VARIABLES:
================
WL:          Wavelengths [nm]
PARA_PRO:    Prospect4/5 Parameters (N,Cab,Cw,Cm[,Car[,Cbrown]])
             4 parameters for Pro4, 5 params for Pro5, 6 params for Pro5B
             7 Params for ProD (N,Cab,Car,Ant,Brown,Cw,Cm) (different
             order!)
PARA_INFORM: Canopy Input Parameters (LAI, LAI_U, SD, H, CD, ALA, Scale)
T_O:         Observation Zenith Angle [°]
T_S:         Illumination Zenith Angle [°]
PSI:         Relative Azimuth between Observation and Illumination [°]
SKYL:        Skylight fraction of total illumination
R_SOIL:      Soil Reflectance
HOT:         Sail Hot Spot Parameter (Leaf Length / Canopy Length)
# %
Examplary Call
wl = (400:10:2500)'; soil = sqrt(wl)/100;
p_pro=[1.5, 40, 0.02, 0.004, 10, 0.5];p_inf=[4, 0.5, 3500, 20, 6, 25, 1];
R=inform_prospect45(wl, p_pro, p_inf, 0, 40, 30, .1, soil, 0.005);
#
Variable	                          Designation       Unit	    Default value
Single tree leaf area index           lai             m2 m-2      7
Leaf area index of understorey	    laiu	        m2 m-2	    0.1
Stem density                          sd              ha-1        650
Tree height                           h               m           20
Crown diameter                        cd              m           4.5
Average leaf angle of tree canopy	    ala	            deg	        55
Scale factor for soil reflectance     scale                       1
# %
External Input Parameters
Variable	                          Designation       Unit	    Default value
Sun zenith angle 	                    theta_s	        deg	        30
Observation zenith angle 	            theta_o	        deg	        0
Azimuth angle	                        psi	            deg	        0
Fraction of diffuse radiation	        skyl	        fraction	0.1
# %
Other Input Data
Variable	                          Designation
r_soil                                Soil spectrum
_____________________________________________________________________________________________________________
# %
OUTPUT VARIABLES
Variable	                          Designation
Forest reflectance                    r_forest
Soil reflectance                      r_soil
Understorey reflectance               r_understorey
Infinite canopy reflectance           r_c_inf
Crown closure                         co
Crown factor                          C
Ground factor                         G
leaf reflectance                    r_leaf
leaf transmittance                  t_leaf
Crown transmittance for theta_s        t_s
Crown transmittance for theta_o        t_o
_____________________________________________________________________________________________________________
#
Atzberger, C. 2000: Development of an invertible forest reflectance model: The INFOR-Model.
In: Buchroithner (Ed.): A decade of trans-european remote sensing cooperation. Proceedings
of the 20th EARSeL Symposium Dresden, Germany, 14.-16. June 2000: 39-44.
# %
Schlerf, M. & Atzberger, C. (2005): Inversion of a forest reflectance model to estimate biophysical
canopy variables from hyperspectral remote sensing data. Submitted to Remote Sensing of Environment.
# %
Rosema, A., Verhoef, W., Noorbergen, H. 1992: A new forest light interaction model in support of forest
monitoring. Remote Sensing of Environment, 42: 23-41.
# %
Jacquemoud, F. & Baret, F. 1990: PROSPECT: A model of leaf optical properties spectra. Remote Sensing of
Environment, 34: 75-91.
# %
Verhoef, W. 1984: Light scattering by leaf layers with application to canopy reflectance modeling: The
SAIL model. Remote Sensing of Environment, 16: 125-141.
#
Basic version of INFORM: Clement Atzberger, 1999
Implementation of LIBERTY: Sebastian Mader, 2002
INFORM modifications and validation: Martin Schlerf, 2004
Coupling INFORM with Prospect4/5: Henning Buddenbaum, 2012
_________________________________________________________________________
"""

from lmuvegetationapps.Resources.PROSAIL.dataSpec import *


class INFORM:

    lambd = len(lambd)

    def __init__(self, tts, tto, psi):

        self.tts = tts
        self.tto = tto
        self.psi = psi

        self.sintts = np.sin(tts)
        self.sintto = np.sin(tto)
        self.costts = np.cos(tts)
        self.costto = np.cos(tto)
        self.tantts = np.tan(tts)
        self.tantto = np.tan(tto)
        self.cospsi = np.cos(psi)

    def inform(self, cd, sd, h, sail_u, sail_inf, sail_tts_trans, sail_tto_trans):

        adapt = 1
        # adapt = 0.6
        k = adapt * (np.pi * np.power((cd / 2), 2)) / 10000

        # Observed ground coverage  by crowns (co) under observation zenith angle theta_o
        co = 1-np.exp(-k*sd/self.costto)
        # Ground coverage by shadow (cs) under a solar zenith angle theta_s
        cs = 1-np.exp(-k*sd/self.costts)
        # Geometrical factor (g) depending on the illumination and viewing geometry
        g = np.power((np.power(self.tantto, 2) + np.power(self.tantts, 2) - 2*self.tantto*self.tantts*self.cospsi), 0.5)
        # Correlation coefficient (p)
        p = np.exp(-g*h/cd)

        # Ground surface fractions (FLIM model)

        # Tree crowns with shadowed background (Fcd)
        Fcd = co * cs + p * np.power((co * (1 - co) * cs * (1 - cs)), 0.5)
        # Tree crowns with sunlit background (Fcs)
        Fcs = co * (1 - cs) - p * np.power((co * (1 - co) * cs * (1 - cs)), 0.5)
        # Shadowed open space (Fod)
        Fod = (1 - co) * cs - p * np.power((co * (1 - co) * cs * (1 - cs)), 0.5)
        # Sunlit open space (Fos)
        Fos = (1 - co) * (1 - cs) + p * np.power((co * (1 - co) * cs * (1 - cs)), 0.5)


        # Forest reflectance (FLIM model)
        # Ground factor (G), that is ground contribution to scene reflectance
        G = Fcd[:, np.newaxis] * sail_tts_trans * sail_tto_trans + Fcs[:, np.newaxis] * sail_tto_trans + \
            Fod[:, np.newaxis] * sail_tts_trans + Fos[:, np.newaxis]

        C = Fcd[:, np.newaxis] * (1 - sail_tts_trans * sail_tto_trans)

        refl_forest = sail_inf * C + sail_u * G

        return refl_forest
