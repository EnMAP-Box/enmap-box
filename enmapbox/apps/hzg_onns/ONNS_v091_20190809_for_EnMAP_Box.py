

import numpy as np
np.seterr(divide='ignore', invalid='ignore')                                    # MH: Ignore RuntimeWarnings

#import gdal, osr
from netCDF4 import Dataset as nc
import os, sys, argparse
#import matplotlib.pyplot as plt
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi2
from datetime import datetime as dt 

sdir        = os.path.dirname(os.path.realpath(__file__))                       # import nnhs from the same directory where we reside, resolving symlinks
sys.path.append(sdir) 

import nnhs


release             = '20190809'                                                # Date of release 
version             = 'v091'                                                    # ONNS Version 



def testbit(n, pos, inv = False):
    
    mask = 1 << pos-1
    
    if inv:
        return (n & mask) != mask
    else:
        return (n & mask) == mask

                                

def prepare_processor_input_txt(inpath, infile, sensor, txt_ID, txt_columns, txt_header):
    
    # Prepare the input to ONNS from txt data file 
    # Provide valid Rrs (remote sensing reflectance) for 11 ONNS bands or at correct other sensor bands 
    
    # lambda_ONNS     = [400.00, 412.50, 442.50, 490.00, 510.00, 560.00, 620.00, 665.00, 753.75, 778.75, 865.00]  
    # lambda_ONNS_1   = [400, 412.5, 442.5, 490, 510, 560, 620, 665, 755, 777.5, 865]
    
    # lambda_OLCI     = [400.00, 412.50, 442.50, 490.00, 510.00, 560.00, 620.00, 665.00, 673.75, 681.25, 708.75, 753.75, 761.25, 764.38, 767.50, 778.75, 865.00, 885.00, 900.00, 940.00, 1020.00]
    
    # colums_ONNS     = [0, 1, 2, 3, 4, 5, 6, 7, 11, 15, 16]                    # MH: fits to lambda_OLCI
    
    
    # lambda_MERIS    = [412.5, 442.5, 490, 510, 560, 620, 665, 755, 777.5, 865]; 
    # lambda_MODIS    = [412, 443, 488, 531, 551, 667, 748, 869.5];
    # lambda_SeaWiFS  = [412, 443, 490, 510, 555, 765, 865];
    # lambda_VIIRS    = [412, 445, 488, 555, 746, 865];
    # lambda_SGLI     = [380, 412, 443, 490, 530, 565, 868.5];
    # lambda_OCCCI    = [412, 443, 490, 510, 555];
    # lambda_OCM2     = [414, 441, 486, 510, 556, 620, 740, 865];
    # lambda_GOCI2    = [380, 412, 443, 490, 510, 555, 620, 660, 745, 865];
    # lambda_PACE     = [400, 410, 440, 490, 510, 560, 620, 665, 755, 775, 865]; 
    # lambda_EnMAP    = [423, 444.7, 488.4, 507.8, 558.6, 620.8, 664.7, 755, 777.4, 863]
    

    data            = np.genfromtxt(fname = inpath + infile, skip_header = txt_header, dtype = 'float')


    if txt_ID == 0:                                                            
    
        P_ID            = list(range(1, data.shape[0]+1))                       # MH: if station number is not provided, continuous numbering from 1 
        
    elif txt_ID == 1: 
    
        P_ID            = list(data[:,0])
        
    
    colums          = [x for x in txt_columns] 
    Rrs_in          = data[:,colums]    
    
    Rrs_in          = np.around(Rrs_in, decimals = 6)
        
    #valid           = np.logical_not(Rrs_in)
    
    
    return Rrs_in, P_ID
    


def prepare_processor_input(inpath, infile):
    
    # Prepare the input to ONNS independently of applied atmospheric correction. 
    # Provide masks and geo information and save them. 
    # Provide valid Rrs (remote sensing reflectance) for 11 ONNS bands.
    
    
    #if 'C2R' in infile.upper():
    if ac == 1:
        
        AC              = 'C2RCC_v_0_18'
        
        #flag_names     = 'quality_flags'
        in_varnames     = ('rhow_1', 'rhow_2', 'rhow_3', 'rhow_4', 'rhow_5', 'rhow_6', 'rhow_7', 'rhow_8','rhow_12', 'rhow_16', 'rhow_17')        
        
        scene_in_rhow   = True                                                  # water-leaving reflectances!!! 
        
        ncfile          = nc(os.path.join(inpath, infile), 'r')
        
        lon             = ncfile.variables['lon'][:]
        lat             = ncfile.variables['lat'][:]
        
        # MH: Level 1 quality flags for land, invalid and clouds
        
        qflags          = ncfile['quality_flags']
        l1_flags        = qflags[:]
        
        if isinstance(l1_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l1_flags        = np.ma.getdata(l1_flags)       
        
        cloud           = testbit(l1_flags, 28)
        invalid         = testbit(l1_flags, 26)                                 # MH: only the side edges 
        #land_1          = testbit(l1_flags, 32)                                 # MH: pure land mask (without inland waters) 
                    
        # MH: C2RCC AC generated (Level 2) flags 
        # Order of bits should be correct, but has to be checked in later versions. 
        
        qflags2         = ncfile['c2rcc_flags']
        l2_flags        = qflags2[:]
        
        if isinstance(l2_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l2_flags        = np.ma.getdata(l2_flags)   
        
        cloud_risk      = testbit(l2_flags, 4)                                  # MH: Additional flag for cloud risk (covers more cloud edges)
        rtosa_oos       = testbit(l2_flags, 1)                                  # MH: Rtosa out of scope
        land            = testbit(l2_flags, 32, inv = True)                     # MH: land mask where inland waters are masked out
        
        #total_invalid_mask     = cloud +   invalid + cloud_risk + rtosa_oos + land_1   # MH: inland waters are not masked out
        total_invalid_mask  = cloud +   invalid + cloud_risk + rtosa_oos + land     # MH: with inland waters!
        
        valid           = np.logical_not(total_invalid_mask)
            
            
            
        rrs             = np.empty([np.sum(valid), len(in_varnames)])           # DM: Rrs or rhow ?? Important in application of NN.
        flag_negative   = np.full(valid.shape, False, dtype = bool)
        flag_suspect    = np.full(valid.shape, False, dtype = bool)
    
        for i in range(0, len(in_varnames)):
         
            b               = ncfile.variables[in_varnames[i]][:]
            #b.shape        = valid.shape
            
            flag_negative[b<0]              = True
            
            flag_suspect[b>10 | ~valid]     = True                              # MH: likely not for C2RCC valid: Mask for fill value(65535) but not captured by cloud + invalid + land 
            
            rrs[:, i]                       = b[valid]  
        
        
        ncfile.close()          
        
        
        
    #if 'pol' in infile.lower(): 
    if ac == 2: 
        
        AC              = 'POLYMER_v_4_8'
        
        #flag_names     = 'bitmask'
        in_varnames     = ('Rw400', 'Rw412', 'Rw443', 'Rw490', 'Rw510', 'Rw560', 'Rw620', 'Rw665', 'Rw754', 'Rw779', 'Rw865')       
        
        scene_in_rhow   = True                                                  # water-leaving reflectances!!! 
        
        ncfile          = nc(os.path.join(inpath, infile), 'r')
        
        try:
            lon             = ncfile.variables['longitude'][:]
            lat             = ncfile.variables['latitude'][:]
        except:
            lon             = ncfile.variables['lon'][:]
            lat             = ncfile.variables['lat'][:]
            
  
        qflags          = ncfile['bitmask']
        l1_flags        = qflags[:]
        
        if isinstance(l1_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l1_flags        = np.ma.getdata(l1_flags)
        

        # MH: valid water pixel according Polymer settings = 0, "Case-2" = 1024, "Inconsistency" = 2048
        # "bitmask" description = LAND:1, CLOUD_BASE:2, L1_INVALID:4, NEGATIVE_BB:8, OUT_OF_BOUNDS:16, EXCEPTION:32, THICK_AEROSOL:64, HIGH_AIR_MASS:128, EXTERNAL_MASK:512, CASE2:1024, INCONSISTENCY:2048
        
        land            = (l1_flags == 1)
        cloud           = (l1_flags == 2)
        l1_invalid      = (l1_flags == 4)
        negative_BB     = (l1_flags == 8)
        out_of_bonds    = (l1_flags == 16)
        exception       = (l1_flags == 32)
        thick_aerosol   = (l1_flags == 64)
        high_air_mass   = (l1_flags == 128)
        external_mask   = (l1_flags == 512)
        case2           = (l1_flags == 1024)
        inconsistancy   = (l1_flags == 2028)
        #land_cloud     = (l1_flags == 3)                                       # MH: not defined mask, but labeled with "3" - likely adjacency pixel 
                
        gerade          = (l1_flags%2 == 0)                                      # MH: mask all even numbers                 
        ungerade        = np.logical_not(gerade)                                # MH: finds everything related to "land"
        
        water           = np.logical_not(land)
        
        flag_ac_risk    = (water & ungerade) | case2
        
                
        # MH: in the current version without inland waters (some rivers - not more)!
        invalid_mask    = cloud + l1_invalid + negative_BB + out_of_bonds + land + exception + high_air_mass + external_mask + inconsistancy + thick_aerosol
        
                
        flag_negative   = np.full(land.shape, False, dtype = bool)
        flag_strange    = np.full(land.shape, False, dtype = bool)
        
        
        b                   = ncfile.variables[in_varnames[0]][:]
        flag_strange[b>1]   = True                                              # MH: basically remove any remaining masked data 
        
        
        valid           = np.logical_not(invalid_mask) & np.logical_not(flag_strange)
        
        
        rrs             = np.empty([np.sum(valid), len(in_varnames)])           # DM: Rrs or rhow ?? Important in application of NN.
        
        for i in range(0, len(in_varnames)):
         
            b                   = ncfile.variables[in_varnames[i]][:]
            #b.shape        = valid.shape
            
            flag_negative[b<0]  = True                                          # MH: marks pixel with any negative Rrs value (mostly in the NIR)
            
            b[b>1]              = 0
                        
            rrs[:, i]           = b[valid]  
        
        
        ncfile.close()  
        

#       rrs             = np.absolute(rrs)
        rrs[rrs<0]      = 0.0001                                                # MH: manipulation of Rrs - simple correction of AC overcorrection 
        
        flag_suspect    = (flag_strange & flag_ac_risk)
        
            

    
    #if (AC_test == 'IPF'):
    if ac == 3:
        
        AC              = 'IPF_v_2_23'
        
        in_varnames_1   = ('Oa01_reflectance.nc', 'Oa02_reflectance.nc', 'Oa03_reflectance.nc', 'Oa04_reflectance.nc', 'Oa05_reflectance.nc', 'Oa06_reflectance.nc', 'Oa07_reflectance.nc', 'Oa08_reflectance.nc', 'Oa12_reflectance.nc', 'Oa16_reflectance.nc', 'Oa17_reflectance.nc')
        in_varnames     = ('Oa01_reflectance', 'Oa02_reflectance', 'Oa03_reflectance', 'Oa04_reflectance', 'Oa05_reflectance', 'Oa06_reflectance', 'Oa07_reflectance', 'Oa08_reflectance', 'Oa12_reflectance', 'Oa16_reflectance', 'Oa17_reflectance')
        
        scene_in_rhow   = True 

        
        for i in range(0, len(in_varnames)):
            
            if i == 0:
                
                ncfile          = nc(os.path.join(inpath, 'geo_coordinates.nc'), 'r')
                
                lon             = ncfile.variables['longitude'][:]
                lat             = ncfile.variables['latitude'][:]       
                
                ncfile.close()
                
                
                ncfile          = nc(os.path.join(inpath, 'wqsf.nc'), 'r')
                
                qflags          = ncfile['WQSF']
                l1_flags        = qflags[:]         
                
                if isinstance(l1_flags, np.ma.MaskedArray):                     # MH: bug fix for py netcdf4 version inconsistency 
                    l1_flags        = np.ma.getdata(l1_flags)
                        
                cloud           = testbit(l1_flags, 4)                          # MH: very likely clouds! to be checked! 
                invalid         = testbit(l1_flags, 1)                          # MH: cut of left and right edges  

                
                land            = testbit(l1_flags, 2, inv = True)              # MH: mask of land and in-land waters 
                
        
                total_invalid_mask  = cloud +   invalid + land                  # MH: ??? to be checked! 
        
                valid           = np.logical_not(total_invalid_mask)                        
                
                ncfile.close()
                
                
                        
                flag_negative   = np.full(valid.shape, False, dtype = bool)
                flag_suspect    = np.full(valid.shape, False, dtype = bool)
                
                # creation of a new "valid" using the first band 
                ncfile          = nc(os.path.join(inpath, in_varnames_1[i]), 'r')
                
                b               = ncfile.variables[in_varnames[i]][:]
                
                flag_negative[b<0]              = True                          # MH: Mask for negative reflectances
                flag_suspect[b>10 | ~valid]     = True                          # MH: Mask for fill value(65535) but not captured by cloud + invalid + land 
                
                valid[flag_suspect & valid]     = False 
                valid[flag_negative]            = False 
                
                
                rrs             = np.empty([np.sum(valid), len(in_varnames)])   # DM: Rrs or rhow ?? Important in application of NN.


                
            if i > 0:
            
                ncfile          = nc(os.path.join(inpath, in_varnames_1[i]), 'r')
            
                b               = ncfile.variables[in_varnames[i]][:]

            
            rrs[:, i]       = b[valid]
            
            ncfile.close()
            
            
            flag_negative[b<0]          = True                                  # MH: sometimes other bands than first band have negative values 
    
    
            
    # Rrs or water leaving reflectance? 
    # Rrs_ONNS only at 11 ONNS bands 
    
    if scene_in_rhow:       
        Rrs_in          = rrs/np.pi
        
    else:       
        Rrs_in          = rrs

    
    Rrs_in          = np.around(Rrs_in, decimals = 6)
    
    
    # Provides all relevant outputs to other functions 
    return Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect




def prepare_processor_input_MERIS(inpath, infile):
    
    # Prepare the input to ONNS independently of applied atmospheric correction. 
    # Provide masks and geo information and save them. 
    # Provide valid Rrs (remote sensing reflectance) for 11 ONNS bands.
    
    # rhown = Normalized water leaving reflectances
    # rhow = Atmospherically corrected Angular dependent water leaving reflectances
    
    #if 'C2R' in infile.upper():
    if ac == 1:
        
        #AC             = 'C2RCC_v_0_18'
        AC              = 'C2RCC_v_0_10'
                
        #in_varnames    = ('rhow_1', 'rhow_2', 'rhow_3', 'rhow_4', 'rhow_5', 'rhow_6', 'rhow_7', 'rhow_10','rhow_12', 'rhow_13')        
        in_varnames     = ('rhown_1', 'rhown_2', 'rhown_3', 'rhown_4', 'rhown_5', 'rhown_6', 'rhown_7', 'rhown_10','rhown_12', 'rhown_13')        
        
        scene_in_rhow   = True                                                  # water-leaving reflectances!!! 
        
        ncfile          = nc(os.path.join(inpath, infile), 'r')
        
        ncfile.set_auto_mask(False)                                             # MH: for py netcdf4 since v1.2.X ?! to be tested!!!        
        
        lon             = ncfile.variables['lon'][:]
        lat             = ncfile.variables['lat'][:]
        
        #print type(lat)
        
        # MH: Level 1 quality flags for land, invalid and clouds
        
        l1_flags        = ncfile.variables['l1_flags'][:]
        
        if isinstance(l1_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l1_flags        = np.ma.getdata(l1_flags)       
        
        cloud           = testbit(l1_flags, 6)                                  # MH: this is actually for BRIGHT - no real cloud mask!!!
        invalid         = testbit(l1_flags, 8)                                  # MH: only the side edges 
                    
        # MH: C2RCC AC generated (Level 2) flags 
        # Order of bits should be correct, but has to be checked in later versions. 
        
        qflags2         = ncfile['c2rcc_flags']
        l2_flags        = qflags2[:]
        
#       if isinstance(l2_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
#           l2_flags        = np.ma.getdata(l2_flags)   
        
        cloud_risk      = testbit(l2_flags, 4)                                  # MH: Additional flag for cloud risk (covers more cloud edges)
        rtosa_oos       = testbit(l2_flags, 1)                                  # MH: Rtosa out of scope
        land            = testbit(l2_flags, 32, inv = True)                     # MH: land mask where inland waters are masked out
        
        
        total_invalid_mask  = cloud +   invalid + cloud_risk + rtosa_oos + land     # MH: with inland waters!
        
        valid           = np.logical_not(total_invalid_mask)
            
            
            
        rrs             = np.zeros([np.sum(valid), 11])                         # DM: Rrs or rhow ?? Important in application of NN.
        flag_negative   = np.full(valid.shape, False, dtype = bool)
        flag_suspect    = np.full(valid.shape, False, dtype = bool)
    
        for i in range(0, len(in_varnames)):
         
            b               = ncfile.variables[in_varnames[i]][:]
            
            flag_negative[b<0]              = True
            
            flag_suspect[b>10 | ~valid]     = True                              # MH: likely not for C2RCC valid: Mask for fill value(65535) but not captured by cloud + invalid + land 
            
            rrs[:, i+1]                     = b[valid]  
        
        
        ncfile.close()          
        
        
        
    #if 'pol' in infile.lower(): 
    if ac == 2: 
        
        AC              = 'POLYMER_v_4_8'
        
        in_varnames     = ('Rw412', 'Rw443', 'Rw490', 'Rw510', 'Rw560', 'Rw620', 'Rw665', 'Rw754', 'Rw779', 'Rw865')        
        
        scene_in_rhow   = True                                                  # water-leaving reflectances!!! 
        
        ncfile          = nc(os.path.join(inpath, infile), 'r')
        
        lon             = ncfile.variables['longitude'][:]
        lat             = ncfile.variables['latitude'][:]
  
        qflags          = ncfile['bitmask']
        l1_flags        = qflags[:]
        
        if isinstance(l1_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l1_flags        = np.ma.getdata(l1_flags)
        
        
        # MH: valid water pixel according Polymer settings = 0, "Case-2" = 1024, "Inconsistency" = 2048
        # "bitmask" description = LAND:1, CLOUD_BASE:2, L1_INVALID:4, NEGATIVE_BB:8, OUT_OF_BOUNDS:16, EXCEPTION:32, THICK_AEROSOL:64, HIGH_AIR_MASS:128, EXTERNAL_MASK:512, CASE2:1024, INCONSISTENCY:2048
        
        land            = (l1_flags == 1)
        cloud           = (l1_flags == 2)
        l1_invalid      = (l1_flags == 4)
        negative_BB     = (l1_flags == 8)
        out_of_bonds    = (l1_flags == 16)
        exception       = (l1_flags == 32)
        thick_aerosol   = (l1_flags == 64)
        high_air_mass   = (l1_flags == 128)
        external_mask   = (l1_flags == 512)
        case2           = (l1_flags == 1024)
        inconsistancy   = (l1_flags == 2028)
        #land_cloud     = (l1_flags == 3)                                       # MH: not defined mask, but labeled with "3" - likely adjacency pixel 
                
        gerade          = (l1_flags%2 == 0)                                     # MH: mask all even numbers                 
        ungerade        = np.logical_not(gerade)                                # MH: finds everything related to "land"
        
        water           = np.logical_not(land)
        
        flag_ac_risk    = (water & ungerade) | case2
        
                
        # MH: in the current version without inland waters (some rivers - not more)!
        invalid_mask    = cloud + l1_invalid + negative_BB + out_of_bonds + land + exception + high_air_mass + external_mask + inconsistancy + thick_aerosol
        
                
        flag_negative   = np.full(land.shape, False, dtype = bool)
        flag_strange    = np.full(land.shape, False, dtype = bool)
        
        
        b                   = ncfile.variables[in_varnames[0]][:]
        flag_strange[b>1]   = True                                              # MH: basically remove any remaining masked data 
        
        
        valid           = np.logical_not(invalid_mask) & np.logical_not(flag_strange)
        
        
        rrs             = np.empty([np.sum(valid), 11])                         # DM: Rrs or rhow ?? Important in application of NN.
        
        for i in range(0, len(in_varnames)):
         
            b                   = ncfile.variables[in_varnames[i]][:]
            #b.shape        = valid.shape
            
            flag_negative[b<0]  = True                                          # MH: marks pixel with any negative Rrs value (mostly in the NIR)
            
            b[b>1]              = 0
                        
            rrs[:, i+1]         = b[valid]  
        
        
        ncfile.close()  
        
#       rrs             = np.absolute(rrs)
        rrs[rrs<0]      = 0.0001                                                # MH: manipulation of Rrs - simple correction of AC overcorrection 
        
        flag_suspect    = (flag_strange & flag_ac_risk)
        

            
    # Rrs or water leaving reflectance? 
    # Rrs_ONNS only at 11 ONNS bands 
    
    if scene_in_rhow:       
        Rrs_in          = rrs/np.pi
        
    else:       
        Rrs_in          = rrs

    
    
    # Provides all relevant outputs to other functions 
    return Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect


    
def prepare_processor_input_MODIS(inpath, infile):
    
    # Prepare the input to ONNS independently of applied atmospheric correction. 
    # Provide masks and geo information and save them. 
    # Provide valid Rrs (remote sensing reflectance) for 11 ONNS bands.
    
    # rhown = Normalized water leaving reflectances
    # rhow = Atmospherically corrected Angular dependent water leaving reflectances
            
        
    #if 'POL' in infile.upper() or 'pol' in infile.lower(): 
    if ac == 2: 
        
        AC              = 'POLYMER_v_4_8'
        
        #in_varnames     = ('Rw412', 'Rw443', 'Rw490', 'Rw510', 'Rw560', 'Rw620', 'Rw665', 'Rw754', 'Rw779', 'Rw865')        
        in_varnames     = ('Rw412', 'Rw443', 'Rw488', 'Rw531', 'Rw547', 'Rw667', 'Rw748', 'Rw869')        
        
        scene_in_rhow   = True                                                  # water-leaving reflectances!!! 
        
        ncfile          = nc(os.path.join(inpath, infile), 'r')
        
        lon             = ncfile.variables['longitude'][:]
        lat             = ncfile.variables['latitude'][:]
  
        qflags          = ncfile['bitmask']
        l1_flags        = qflags[:]
        
        if isinstance(l1_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l1_flags        = np.ma.getdata(l1_flags)
        
        
        # MH: valid water pixel according Polymer settings = 0, "Case-2" = 1024, "Inconsistency" = 2048
        # "bitmask" description = LAND:1, CLOUD_BASE:2, L1_INVALID:4, NEGATIVE_BB:8, OUT_OF_BOUNDS:16, EXCEPTION:32, THICK_AEROSOL:64, HIGH_AIR_MASS:128, EXTERNAL_MASK:512, CASE2:1024, INCONSISTENCY:2048
        
        land            = (l1_flags == 1)
        cloud           = (l1_flags == 2)
        l1_invalid      = (l1_flags == 4)
        negative_BB     = (l1_flags == 8)
        out_of_bonds    = (l1_flags == 16)
        exception       = (l1_flags == 32)
        thick_aerosol   = (l1_flags == 64)
        high_air_mass   = (l1_flags == 128)
        external_mask   = (l1_flags == 512)
        case2           = (l1_flags == 1024)
        inconsistancy   = (l1_flags == 2028)
        #land_cloud     = (l1_flags == 3)                                       # MH: not defined mask, but labeled with "3" - likely adjacency pixel 
                
        gerade          = (l1_flags%2 == 0)                                     # MH: mask all even numbers                 
        ungerade        = np.logical_not(gerade)                                # MH: finds everything related to "land"
        
        water           = np.logical_not(land)
        
        flag_ac_risk    = (water & ungerade) | case2
        
                
        # MH: in the current version without inland waters (some rivers - not more)!
        invalid_mask    = cloud + l1_invalid + negative_BB + out_of_bonds + land + exception + high_air_mass + external_mask + inconsistancy + thick_aerosol
        
                
        flag_negative   = np.full(land.shape, False, dtype = bool)
        flag_strange    = np.full(land.shape, False, dtype = bool)
        
        
        b                   = ncfile.variables[in_varnames[0]][:]
        flag_strange[b>1]   = True                                              # MH: basically remove any remaining masked data 
        
        
        valid           = np.logical_not(invalid_mask) & np.logical_not(flag_strange)
        
        
        #rrs             = np.empty([np.sum(valid), 11])                         # DM: Rrs or rhow ?? Important in application of NN.
        rrs             = np.empty([np.sum(valid), len(in_varnames)])            # DM: Rrs or rhow ?? Important in application of NN.
        
        for i in range(0, len(in_varnames)):
         
            b                   = ncfile.variables[in_varnames[i]][:]
            #b.shape        = valid.shape
            
            flag_negative[b<0]  = True                                          # MH: marks pixel with any negative Rrs value (mostly in the NIR)
            
            b[b>1]              = 0
                        
            #rrs[:, i+1]         = b[valid]  
            rrs[:, i]           = b[valid]  
        
        
        ncfile.close()  
        
#       rrs             = np.absolute(rrs)
        rrs[rrs<0]      = 0.0001                                                # MH: manipulation of Rrs - simple correction of AC overcorrection 
        
        flag_suspect    = (flag_strange & flag_ac_risk)
        

            
    # Rrs or water leaving reflectance? 
    # Rrs_ONNS only at 11 ONNS bands 
    
    if scene_in_rhow:       
        Rrs_in          = rrs/np.pi
        
    else:       
        Rrs_in          = rrs

    
    
    # Provides all relevant outputs to other functions 
    return Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect



def prepare_processor_input_VIIRS(inpath, infile):
    
    # Prepare the input to ONNS independently of applied atmospheric correction. 
    # Provide masks and geo information and save them. 
    # Provide valid Rrs (remote sensing reflectance) for 11 ONNS bands.
    
    # rhown = Normalized water leaving reflectances
    # rhow = Atmospherically corrected Angular dependent water leaving reflectances
            
        
    #if 'POL' in infile.upper() or 'pol' in infile.lower(): 
    if ac == 2: 
        
        AC              = 'POLYMER_v_4_8'
        
        #in_varnames     = ('Rw412', 'Rw443', 'Rw490', 'Rw510', 'Rw560', 'Rw620', 'Rw665', 'Rw754', 'Rw779', 'Rw865')        
        in_varnames     = ('Rw410', 'Rw443', 'Rw486', 'Rw551', 'Rw745', 'Rw862')        
        
        scene_in_rhow   = True                                                  # water-leaving reflectances!!! 
        
        ncfile          = nc(os.path.join(inpath, infile), 'r')
        
        lon             = ncfile.variables['longitude'][:]
        lat             = ncfile.variables['latitude'][:]
  
        qflags          = ncfile['bitmask']
        l1_flags        = qflags[:]
        
        if isinstance(l1_flags, np.ma.MaskedArray):                             # MH: bug fix for py netcdf4 version inconsistency 
            l1_flags        = np.ma.getdata(l1_flags)
        
        
        # MH: valid water pixel according Polymer settings = 0, "Case-2" = 1024, "Inconsistency" = 2048
        # "bitmask" description = LAND:1, CLOUD_BASE:2, L1_INVALID:4, NEGATIVE_BB:8, OUT_OF_BOUNDS:16, EXCEPTION:32, THICK_AEROSOL:64, HIGH_AIR_MASS:128, EXTERNAL_MASK:512, CASE2:1024, INCONSISTENCY:2048
        
        land            = (l1_flags == 1)
        cloud           = (l1_flags == 2)
        l1_invalid      = (l1_flags == 4)
        negative_BB     = (l1_flags == 8)
        out_of_bonds    = (l1_flags == 16)
        exception       = (l1_flags == 32)
        thick_aerosol   = (l1_flags == 64)
        high_air_mass   = (l1_flags == 128)
        external_mask   = (l1_flags == 512)
        case2           = (l1_flags == 1024)
        inconsistancy   = (l1_flags == 2028)
        #land_cloud     = (l1_flags == 3)                                       # MH: not defined mask, but labeled with "3" - likely adjacency pixel 
                
        gerade          = (l1_flags%2 == 0)                                     # MH: mask all even numbers                 
        ungerade        = np.logical_not(gerade)                                # MH: finds everything related to "land"
        
        water           = np.logical_not(land)
        
        flag_ac_risk    = (water & ungerade) | case2
        
                
        # MH: in the current version without inland waters (some rivers - not more)!
        invalid_mask    = cloud + l1_invalid + negative_BB + out_of_bonds + land + exception + high_air_mass + external_mask + inconsistancy + thick_aerosol
        
                
        flag_negative   = np.full(land.shape, False, dtype = bool)
        flag_strange    = np.full(land.shape, False, dtype = bool)
        
        
        b                   = ncfile.variables[in_varnames[0]][:]
        flag_strange[b>1]   = True                                              # MH: basically remove any remaining masked data 
        
        
        valid           = np.logical_not(invalid_mask) & np.logical_not(flag_strange)
        
        
        #rrs             = np.empty([np.sum(valid), 11])                         # DM: Rrs or rhow ?? Important in application of NN.
        rrs             = np.empty([np.sum(valid), len(in_varnames)])            # DM: Rrs or rhow ?? Important in application of NN.
        
        for i in range(0, len(in_varnames)):
         
            b                   = ncfile.variables[in_varnames[i]][:]
            #b.shape        = valid.shape
            
            flag_negative[b<0]  = True                                          # MH: marks pixel with any negative Rrs value (mostly in the NIR)
            
            b[b>1]              = 0
                        
            #rrs[:, i+1]         = b[valid]  
            rrs[:, i]           = b[valid]  
        
        
        ncfile.close()  
        
#       rrs             = np.absolute(rrs)
        rrs[rrs<0]      = 0.0001                                                # MH: manipulation of Rrs - simple correction of AC overcorrection 
        
        flag_suspect    = (flag_strange & flag_ac_risk)
        

            
    # Rrs or water leaving reflectance? 
    # Rrs_ONNS only at 11 ONNS bands 
    
    if scene_in_rhow:       
        Rrs_in          = rrs/np.pi
        
    else:       
        Rrs_in          = rrs

    
    
    # Provides all relevant outputs to other functions 
    return Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect




def sensor_band_adapter(path_to_NN, Rrs_in, sensor, adapt):
        
    ###
    # Transformation of NN input data - must be remote-sensing reflectance 
    
    rrs             = np.log10(Rrs_in + 0.001)
    
    
    if sensor == 'OLCI':
        
        #netz            = 'Testnetz_Adapter_MERIS_97x77x37_0.8.net'
        netz            = 'MERIS_97x77x37_0.8.net'
        
        if (adapt == 1):                                                        # MH: Option that only 400 band is replaced
        
            nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz))
            
            out1            = np.zeros([Rrs_in.shape[0], 11])
            
            for l in range(rrs.shape[0]):
                
                input           = np.hstack([rrs[l, 1:]])
                out1[l, :]      = nn3.ff_nnhs(input)        
                
                
            Rrs_ONNS_new        = np.zeros(out1.shape)
            
            Rrs_ONNS_new[:, 0]  = 10**out1[:, 0] - 0.001                     
            Rrs_ONNS_new[:,1:]  = np.copy(Rrs_in[:,1:])
            
            
        elif (adapt == 2):                                                      # MH: Option that all Rrs are replaced
                        
            nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz))
            
            out1            = np.zeros([Rrs_in.shape[0], 11])
            
            for l in range(rrs.shape[0]):
                
                input       = np.hstack([rrs[l, 1:]])
                out1[l, :]      = nn3.ff_nnhs(input)        
                
                
            Rrs_ONNS_new        = np.zeros(out1.shape)

            Rrs_ONNS_new[:,:]   = 10**out1[:,:] - 0.001                     
            
        else:                                                                   # MH: no band adaptation

            Rrs_ONNS_new        = np.copy(Rrs_in)
            
            
            
    elif sensor == 'MERIS':     
            
        #netz            = 'Testnetz_Adapter_MERIS_97x77x37_0.8.net'
        netz            = 'MERIS_97x77x37_0.8.net'
        
        if (adapt == 1):                                                        # MH: Option that only 400 band is replaced
        
            nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz))
            
            out1            = np.zeros([Rrs_in.shape[0], 11])
            
            for l in range(rrs.shape[0]):
                
                input           = np.hstack([rrs[l, :]])
                out1[l, :]      = nn3.ff_nnhs(input)        
                
                
            Rrs_ONNS_new        = np.zeros(out1.shape)
            
            Rrs_ONNS_new[:, 0]  = 10**out1[:, 0] - 0.001                     
            Rrs_ONNS_new[:,1:]  = np.copy(Rrs_in)
            
            
        elif (adapt == 2):                                                      # MH: Option that all Rrs are replaced
                        
            nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz))
            
            out1            = np.zeros([Rrs_in.shape[0], 11])
            
            for l in range(rrs.shape[0]):
                
                input       = np.hstack([rrs[l, :]])
                out1[l, :]      = nn3.ff_nnhs(input)        
                
                
            Rrs_ONNS_new        = np.zeros(out1.shape)

            Rrs_ONNS_new[:,:]   = 10**out1[:,:] - 0.001                     

        
    else: 
        
        if sensor == 'MODIS':
            
            netz            = 'MODIS_37x77x97_1.2.net'
            
        elif sensor == 'VIIRS':
            
            netz            = 'VIIRS_23x41x59x43_1.7.net'
            
        elif sensor == 'SGLI':
            
            netz            = 'SGLI_37x77x97_1.4.net'
            
        elif sensor == 'SeaWiFS_OCCCI':
            
            netz            = 'SeaWiFS_OCCCI_37x77x97_56.4.net'
            
        elif sensor == 'SeaWiFS':
            
            netz            = 'SeaWiFS_23x76x55x36_1.4.net'
            
        elif sensor == 'PACE':
            
            netz            = 'PACE_37x77x97_0.7.net'
            
        elif sensor == 'OCM2':
            
            netz            = 'OCM2_37x77x97_1.2.net'
            
        elif sensor == 'GOCI2':
            
            netz            = 'GOCI2_37x77x97_0.8.net'
            
        elif sensor == 'EnMAP':
            
            netz            = 'EnMAP_97x77x37_1.4.net'
            
        else:
            
            print('Error: Sensor not recognized.')
            
        
        
        Rrs_ONNS_new    = np.zeros((rrs.shape[0], 11))
                        
        nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz))
        
        a               = rrs[:, :]                                        
        
        out1            = np.zeros(Rrs_ONNS_new.shape)
        
        for l in range(rrs.shape[0]):
            
            input           = np.hstack([a[l, :]])
            out1[l, :]      = nn3.ff_nnhs(input)        
            
        
        Rrs_ONNS_new[:,:]   = 10**out1[:,:] - 0.001     

        
    
    ###
    # If Adapter NN fails and results in NaNs 
        
    ID                      = np.isnan(Rrs_ONNS_new[:,0])                       
        
    Rrs_ONNS_new[ID,:]      = 0.01
    
        
    flag_adapter_fail       = np.full(rrs.shape[0], False, dtype = bool)

    flag_adapter_fail[ID]   = True
        

    
    Rrs_ONNS                = np.copy(Rrs_ONNS_new)
    
    
        
    return Rrs_ONNS, flag_adapter_fail
    
    
    
def classify_clustering_fuzzy(output_size, Rrs_ONNS, path_to_classes = "./classification/preselect_reducedHL_20161006H1203"):   


    ##
    # Read scene or data.
    
    weights     = (0.1, 0.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8, 0.2)                   # MH: Wheighting of influence of singel wave bands  
    weights     = np.array([np.float(x) for x in weights]) 
 
    
 
    ###
    # read parameters from log-file of Clustering!
    
    f           = open(os.path.join(path_to_classes, "logfile.txt"), 'r')
    test        = f.readlines()
    
    matching    = [s for s in test if "wavelengths" in s][0]
    lam         = [int(s) for s in matching.strip("wavelengths:").split()]
    Nvar        = len(lam)
    
    matching    = [s for s in test if "log.transform" in s][0]
    log_transform   = sum([s == "T" for s in matching.split()]) == 1
    
    addLog      = 0
 
    
    if log_transform:
     
        matching        = [s for s in test if "Offset for Rrs" in s][0]
        addLog          = [float(s) for s in matching.strip("Offset for Rrs:").split()][0]
    
 
    matching    = [s for s in test if "weights" in s]                           # DM: only identify, whether data has to be scaled! Weights are not applied to the data, but in the calculation of the distances!
    scaled      = len(matching) != 0 
    
    matching    = [s for s in test if "variable names" in s][0]
    varnames    = [s for s in matching.strip("variable names: ").split()]
 
    
    matching    = [s for s in test if "Clustering" in s][0] 
    Ncluster    = [int(s) for s in matching.strip("Clustering N=").split()][0]
    
    
 
    ####
    # Special log transformation, in this version, usually addLog = 1 is added to Rrs
        
    if log_transform:
     
        Rrs_ONNS        = np.log10(Rrs_ONNS + addLog)
 
    
    ###
    # Selecting Wavelengths for classification! (might be important to do before scaling! otherwise 'wrong' contributions have still influence.
 
    IDrrs       = list(range(Nvar))
    #IDrrs = np.array(range(1,Nvar)) #omits 400nm
    
    
    
    ####
    # Brightness-scaling of reflectance data
 
    d_all       = np.copy(Rrs_ONNS[:, IDrrs])
 
    
    if scaled:
     
        dsum            = np.sum(Rrs_ONNS[:, IDrrs], axis = 1)
  
        for i in range(0, d_all.shape[1]):
      
            d_all[:,i]      = d_all[:,i]/ dsum 
        
        d_all           = np.c_[d_all, dsum]
  
    else: 
     
        d_all           = Rrs_ONNS[:,IDrrs]
        
    
 
    ####
    # Read Covariance + Cluster means
 
    filename    = os.path.join(path_to_classes,'class_cov.nc')
    a           = nc(filename)
    new_covs    = np.array(a['covariance'])
    a.close()
    
    filename    = os.path.join(path_to_classes, 'class_means.nc')
    a           = nc(filename)
    new_means   = np.array(a['cluster_means'])
    a.close()
    
    class_name  = path_to_classes.split('/')[-1]
    
    
    
    ####
    # Calculate weighted distances!
        
    dist        = np.empty([Rrs_ONNS.shape[0], Ncluster])
    m           = np.empty([Rrs_ONNS.shape[0], Ncluster])    
    
    
    for i in range(0,Ncluster):
       
        VI              = np.copy(new_covs[i, :, :][IDrrs, :][:, IDrrs])                # covariance matrix
  
        
        # diagonale
        diagVI          = np.diag(VI)
        
        if scaled: 
      
            dist[:,i]       = np.apply_along_axis(lambda x: np.sum( weights*(x-new_means[0:(Nvar),i])**2/diagVI), 1, d_all[:, 0:(Nvar)] ) #pseudo-mahalanobis with weights!
   
        else:
      
            dist[:,i]       = np.apply_along_axis(lambda x: mahalanobis(u=x, v=new_means[0:(Nvar), i], VI=vi)**2, 1, d_all[:, 0:(Nvar)] )
        
  
        m[:,i]          = 1 - chi2.cdf(x = dist[:, i], df = Nvar)
  
        
    
    total_membership = np.apply_along_axis(lambda x: np.sum(x), 1, m )
    
    maxMemb         = np.apply_along_axis(lambda x: np.array(list(range(1, Ncluster+1)))[x == np.max(x)][0], 1, m)
    
    id              = np.apply_along_axis(lambda x: np.max(x), 1, m) > 10**-9
 
    maxMemb[np.logical_not(id)]    = 0
    
    
        
    ####
    # Save figures with memberships and their frequency for overview    
    
    # if (output_size == 2) and (not ('txt' in infile.lower())):
    #
    #     bins        = np.linspace(0, Ncluster + 1)
    #
    #     plt.hist(maxMemb, bins = bins)
    #     plt.savefig(os.path.join(outpath, 'maxMembDistr_' + class_name + "_" + infile + '.png'), dpi = 500)      # save the figure to file
    #     plt.close()
    #
    #
    #     test2           = np.empty(valid.shape)
    #     test2[valid]    = maxMemb
    #     test2           = np.ma.array(test2, mask = np.logical_not(valid), dtype = 'int')
    #
    #     cmap        = plt.cm.get_cmap('jet')
    #     img         = plt.imshow(test2, interpolation = 'nearest', cmap = cmap)
    #     cb          = plt.colorbar(img, shrink = 0.8)
    #
    #     plt.savefig(os.path.join(outpath, 'maxMemb_' + class_name + "_" + infile + '.png'), dpi = 500)           # save the figure to file
    #     plt.close()
    #
    #
    #     out         = np.zeros(valid.shape)
    #     out[valid]  = total_membership
    #     out         = np.ma.array(out, mask = np.logical_not(valid), dtype = 'int')
    #
    #     cmap        = plt.cm.get_cmap('jet')
    #     img         = plt.imshow(out, interpolation = 'nearest', cmap = cmap)
    #     cb          = plt.colorbar(img, shrink = 0.8)
    #
    #     plt.savefig(os.path.join(outpath, 'TotalMemb_' + class_name + "_" + infile + '.png'), dpi = 500)         # save the figure to file
    #     plt.close()
    #
    

    ###
    # Calculate proportional weights for ONNS application 
    
    m2          = np.copy(m)
    
    id          = m2 < 10**-4                                                   # MH: this weight threshold is from Moore et al. 2001, if it is 10**-5, more pixel are valid 
    m2[id]      = 0
    
    total_membership    = np.apply_along_axis(lambda x: np.sum(x), 1, m2 )      # MH: total membership can be above 1 
    
    # maxMemb   = np.apply_along_axis(lambda x: np.array(range(1, Nclass + 1))[x == np.max(x)][0], 1, m)
    
    
    for i in range(m2.shape[1]):
        
        m2[:,i]         = m2[:,i]/ total_membership                             # MH: if there is any membership (total_membership > 0), than new total_membership is 1

    
    ### 
    # New flags depending on classification 
    
    flag_nonclassify    = np.full(m2.shape[0], False, dtype = bool)
    flag_lowmember_01   = np.full(m2.shape[0], False, dtype = bool)
    flag_lowmember_03   = np.full(m2.shape[0], False, dtype = bool)
    flag_lowmember_09   = np.full(m2.shape[0], False, dtype = bool)
    flag_lowmember_05   = np.full(m2.shape[0], False, dtype = bool)
    
    flag_nonclassify[np.sum(m2,1) == 0]         = True                          # MH: pixel that is not classifyable 
    flag_lowmember_01[total_membership < 0.1]   = True                          # MH: pixel with insignificantly low total memberships 
    flag_lowmember_03[total_membership < 0.3]   = True                          # MH: pixel with low total memberships 
    flag_lowmember_09[total_membership < 0.9]   = True                          # MH: pixel with relatively low total memberships 
    flag_lowmember_05[np.max(m2,1) < 0.5]       = True                          # MH: pixel where max memberships is below 0.5
    
    
    flag_ONNS_valid     = np.full(m2.shape[0], True, dtype = bool)
    
    #flag_ONNS_valid[flag_nonclassify | flag_lowmember_09]  = False             # MH: pixel where all ONNS results are valid 
    flag_ONNS_valid[flag_nonclassify | flag_lowmember_03]   = False             # MH: pixel where all ONNS results are valid 

    
    
    return m, m2, total_membership, maxMemb, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid




def ONNS(path_to_NN, Rrs_ONNS, m2):
        
    ###
    # Transformation of NN input data - must be remote-sensing reflectance 
    
    rrs             = np.log10(Rrs_ONNS + 0.001)
        

    # Actual application of NNs 
    
    NNtype          = ['Conc', 'FUKd', 'IOPs']
    
    # MH: variables CDOM and a_g_440 are quasi identical, only from different sets of NNs 
    
        
    total_out_weighted      = np.zeros((rrs.shape[0], 13))                      # MH: 13 is number of total output off all 3 networks 
    
    
    for nntype in NNtype:
    
        netnames        = os.listdir(path_to_NN)
        netnames.sort()                                                         # MH: IMPORTANT to have the correct order of files for OWT 1 to 13 
        
        netnames        = [s for s in netnames if s[0]!="."]
        netnames        = [s for s in netnames if nntype in s ]
        

        nn2             = nnhs.nnhs(os.path.join(path_to_NN, netnames[0]))
        outvar          = nn2.outvar

        
        
        ###
        # Calculate NN output per water class
        
        # largest 3D matrix - danger of memory error! 
        # MH: Initialize output matix: number of spectra, number of OWTs, number of NN outputs
                
        total_out           = np.zeros((rrs.shape[0], 13, nn2.noutp))           # MH: 13 here is number of OWTs 
        Chl_unweighted      = np.zeros((rrs.shape[0], 13))                      # MH: unweighted Chl per OWT 
            
        for NNname,i in zip(netnames, list(range(13))):
                        
            ID              = m2[:,i] > 0
                        
            nn2             = nnhs.nnhs(os.path.join(path_to_NN, NNname))
            
            out1            = np.zeros((np.sum(ID), nn2.noutp))*np.nan
            
            a               = rrs[ID,:]                                         # MH: log-transformed Rrs + 0.001
            
            for l in range(np.sum(ID)):
                
                input           = np.hstack([a[l, :]])
                out1[l, :]      = nn2.ff_nnhs(input)
            
            
            for k in range(nn2.noutp):
                
                total_out[ID, i, k]     = out1[:, k]
        
                    
            del out1                                                            # MH: clear workspace 
            
            
        
        ###
        # Combine NN results with memberships per water class and write to nc-product.
        # MH: small differences occur depending where the wheighting of results is applied
        # before or after back-logarithmization: after weighting is more logical, 
        # since NN training and classification is based on same format
        # MH: normally it runs first 'Conc', then 'FUKd', and last 'IOPs' but order is important for BIAS nets
            
        for i in range(len(outvar)):
                            
            if nntype == 'Conc':
                
                a           = total_out[:,:,i]
                
                bbb         = np.zeros(rrs.shape[0], )
                bbb         = np.apply_along_axis(lambda x: np.sum(x), 1, m2*a ) 
                
                bbb         = 10**bbb - 0.001                                   # MH: Transform from log10(X + 0.001)
                
                total_out_weighted[:,i]     = np.copy(bbb)                      # MH: columns 0 to 2
                
                if (i == 0):
                    
                    b               = np.copy(a)
                    Chl_unweighted  = 10**b - 0.001
                
                
            elif nntype == 'FUKd':
                
                a           = total_out[:,:,i]
                
                bbb         = np.zeros(rrs.shape[0], )
                bbb         = np.apply_along_axis(lambda x: np.sum(x), 1, m2*a ) 
                
                if i == 0:                                                      # MH: first variable (FU) is not logarithmized 
                    
                    bbb         = np.round(bbb)
                
                else:
                
                    bbb         = 10**bbb - 0.001                               # MH: Transform from log10(X + 0.001)
                    
                
                total_out_weighted[:,i+8]   = np.copy(bbb)                      # MH: columns 8 to 12 
                
                
            elif nntype == 'IOPs': 
                
                a           = total_out[:,:,i]
                
                bbb         = np.zeros(rrs.shape[0], )
                bbb         = np.apply_along_axis(lambda x: np.sum(x), 1, m2*a ) 
                
                bbb         = 10**bbb - 0.001                                   # MH: Transform from log10(X + 0.001)
                
                total_out_weighted[:,i+3]   = np.copy(bbb)                      # MH: columns 3 to 7
                
            else:
                
                print('Error in ONNS nets application')                         # MH: just in case ... 
                
                
        del a                                                                   # MH: clear workspace 
        del bbb
        del total_out
        
        
    return total_out_weighted, Chl_unweighted
    
    
    
    
def background_NN(path_to_NN, Rrs_ONNS):                                        # MH: alternative NNs that are applied in case of low memberships
        
    ###
    # Transformation of NN input data - must be remote-sensing reflectance 
    
    rrs             = np.log10(Rrs_ONNS + 0.001)
    
    
    ### 
    # Differentiation of two cases 
    
    index_Rrs_max   = np.argmax(Rrs_ONNS, axis=1)                               # MH: finds maximum wavelentgh (index) of Rrs
    
    Case            = index_Rrs_max < 3                                         # MH: finds spectra with max @ lambda < 490 nm      
    
            
    lambda_ONNS     = [400, 412.5, 442.5, 490, 510, 560, 620, 665, 755, 777.5, 865]
    
    
    lambda_Rrs_max  = np.empty([index_Rrs_max.shape[0],])
                
    for i in range(0, index_Rrs_max.shape[0]):  
        
        lambda_Rrs_max[i] = lambda_ONNS[index_Rrs_max[i]]


    
    total_out_bNN   = np.zeros((rrs.shape[0], 13))                              # MH: 13 is number of total output off all 3 networks 

    out1            = np.zeros((rrs.shape[0], 3))
    out2            = np.zeros((rrs.shape[0], 5))
    out3            = np.zeros((rrs.shape[0], 5))   
    
    
    ###
    # Case 1 --> maximum of Rrs <490 nm

    ID              = np.where(Case)[0]                                         # MH: List with Case 1 cases  
    
    netz1           = 'ONNS_20180607_Case1_CON_bNN_23x76x55x36_6.8.net'
    netz2           = 'ONNS_20180607_Case1_FUK_bNN_97x77x37_9.9.net'
    netz3           = 'ONNS_20180607_Case1_IOP_bNN_37x77x97_14.7.net'
        
    nn1             = nnhs.nnhs(os.path.join(path_to_NN, netz1))
    nn2             = nnhs.nnhs(os.path.join(path_to_NN, netz2))
    nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz3))    
    
    
    for l in range(len(ID)):
        
        input           = np.hstack([rrs[ID[l], :]])
        
        out1[ID[l], :]      = nn1.ff_nnhs(input)    
        out2[ID[l], :]      = nn2.ff_nnhs(input)    
        out3[ID[l], :]      = nn3.ff_nnhs(input)    
        
        
    ###
    # Case 2 --> maximum of Rrs >= 490 nm

    ID              = np.where(Case == False)[0]                                # MH: List with Case 2 cases  
    
    netz1           = 'ONNS_20180607_Case2_CON_bNN_23x76x55x36_17.0.net'
    netz2           = 'ONNS_20180607_Case2_FUK_bNN_97x77x37_3.2.net'
    netz3           = 'ONNS_20180607_Case2_IOP_bNN_23x41x59x43_28.6.net'
        
    nn1             = nnhs.nnhs(os.path.join(path_to_NN, netz1))
    nn2             = nnhs.nnhs(os.path.join(path_to_NN, netz2))
    nn3             = nnhs.nnhs(os.path.join(path_to_NN, netz3))    
    
    
    for l in range(len(ID)):
        
        input           = np.hstack([rrs[ID[l], :]])
        
        out1[ID[l], :]      = nn1.ff_nnhs(input)    
        out2[ID[l], :]      = nn2.ff_nnhs(input)    
        out3[ID[l], :]      = nn3.ff_nnhs(input)    
        
        

        
    ###
    # back-log-transform of total results 
        
    for k in range(3):
        
        total_out_bNN[:, k]     = 10**out1[:, k] - 0.001                        # MH: Transform from log10(X + 0.001)
        
        
    for k in range(5):
        
        total_out_bNN[:, k+3]   = 10**out3[:, k] - 0.001                        # MH: Transform from log10(X + 0.001)
        
        
    for k in range(5):
        
        if k == 0: 
            total_out_bNN[:, k+8]   = np.round(out2[:, k])                      # MH: first variable (FU) is not logarithmized
        else: 
            total_out_bNN[:, k+8]   = 10**out2[:, k] - 0.001                    # MH: Transform from log10(X + 0.001)



        
    return total_out_bNN, Case, lambda_Rrs_max
    
    
    
    
def apply_BIAS_NN(path_to_NN, total_out_weighted, m2):
    
        
    ###
    # Reading Results of NNs for IOPs, FU, Conc - combined in one file 

    Variables       = ['Chl', 'ISM', 'a_g_440', 'a_p_440', 'a_m_440', 'b_p_440', 'b_m_440', 'FU', 'K_d_490', 'K_u_490', 'a_dg_412', 'b_bp_510'] 
    #Variables_text = ['Chl_uncertainty', 'ISM_uncertainty', 'a_g_440_uncertainty', 'a_p_440_uncertainty', 'a_m_440_uncertainty', 'b_p_440_uncertainty', 'b_m_440_uncertainty', 'FU_uncertainty', 'K_d_490_uncertainty', 'K_u_490_uncertainty', 'a_dg_412_uncertainty', 'b_bp_510_uncertainty'] 

    
    # MH: order of variable important
    # MH: a_g_440 from IOP nets used for CDOM (CDOM from Conc nets not used)
    # MH: values are already back-logaithmized (not FU)

    
    #input_to_BIAS  = np.empty([np.sum(valid), 12])
    input_to_BIAS   = np.empty([Rrs_ONNS.shape[0], 12])
    
    BIAS_input_variables    = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]           # MH: not 1 (CDOM)
    
    i               = 0
    
    
    for j in BIAS_input_variables: 
        
        input_to_BIAS[:, i]     = total_out_weighted[:,j]
        
        i                       = i + 1
    
                
    total_BIAS_out_weighted     = np.zeros((input_to_BIAS.shape[0], 12))
                
    NNtype      = ['BIAS']
    
    
    for nntype in NNtype:
        
        netnames        = os.listdir(path_to_NN)
        netnames.sort()                                                         # MH: IMPORTANT to have the correct order of files for OWT 1 to 13 
        
        netnames        = [s for s in netnames if s[0]!="."]
        netnames        = [s for s in netnames if nntype in s ]
        
        nn2             = nnhs.nnhs(os.path.join(path_to_NN, netnames[0]))
        
        total_out       = np.zeros((input_to_BIAS.shape[0], 13, nn2.noutp))
                
        
        for NNname,i in zip(netnames, list(range(13))):
            
            ID          = m2[:,i] > 0
            
            nn2         = nnhs.nnhs(os.path.join(path_to_NN, NNname))
            out1        = np.zeros((np.sum(ID), nn2.noutp))*np.nan
            
            a           = input_to_BIAS[ID,:]
            
            
            for l in range(np.sum(ID)):
                
                input           = np.hstack([a[l, :]])
                out1[l, :]      = nn2.ff_nnhs(input)
            
            
            for k in range(nn2.noutp):
                
                total_out[ID, i, k]     = out1[:, k]
        
        
                    
        for i in range(len(Variables)):
                        
            a           = total_out[:,:,i]
            
            b           = np.zeros(m2.shape[0], )
            b           = np.apply_along_axis(lambda x: np.sum(x), 1, m2*a )    # MH: wheighted estimate of BIAS nets
            
            if i == 7:                                                          # MH: must be FU, which is an integer 
                b           = np.round(b)
                                    
                        
            bb          = input_to_BIAS[:,i]
            
            b2          = 100* (bb - b)/ b                                      # MH: Error_Chl = 100* (Chl_ONNS - Chl_BIAS)./Chl_BIAS

            total_BIAS_out_weighted[:,i]    = np.copy(b2)  
            

    return total_BIAS_out_weighted  




def merge_products(total_membership, total_out_weighted, total_out_bNN, Case):
    
    
    total_out_merged        = np.copy(total_out_weighted)
    
    total_out_merged[total_membership < 0.3, :] = np.copy(total_out_bNN[total_membership < 0.3, :])
    
    
    
    flag_Case_bNN           = np.zeros(total_out_weighted.shape[0]) 
        
    for i in range(len(flag_Case_bNN)):
        
        if (Case[i] and total_membership[i] < 0.3):
            
            flag_Case_bNN[i]        = 1
            
        elif (Case[i] == False and total_membership[i] < 0.3):

            flag_Case_bNN[i]        = 2


    total_out_merged    = np.around(total_out_merged, decimals = 4) 
    
    

    return total_out_merged, flag_Case_bNN
    
    


def save_results(outname, maxMemb, m, m2, total_membership, total_out_weighted, total_out_bNN, total_out_merged, total_BIAS_out_weighted, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid, Rrs_ONNS, valid, flag_adapter_fail, flag_Case_bNN, version, output_size, lambda_Rrs_max):
        
        
    # One output file for all processor results 
        
    #out             = nc(outname, 'w', format = 'NETCDF4')
    out             = nc(outname, 'w')
    #out            = nc(outname, 'a')                                          # MH: adds data to existing nc file 
    
    
    # Group_ONNS      = out.createGroup('ONNS_products')
    # Group_l1_flags  = out.createGroup('l1_flags')
    #
    #
    # if (output_size > 0):
    #
    #     Group_OWT       = out.createGroup('OWT')
    #     Group_AC        = out.createGroup('AC')
    #     Group_l2_flags  = out.createGroup('l2_flags')
        
        
    
    ###
    # General information on code and data 
    
    out.title                      = 'ONNS Level-2 ocean color products based on atmospheric corrected satellite data'
    out.source                     = 'remote sensing'
    out.sensor                     = sensor

    if sensor == 'OLCI':
        out.acquisition_start          = str(infile[16:31])
        out.acquisition_stop           = str(infile[32:47])


    out.atmospheric_correction     = AC
    out.creation_date              = str(dt.now())[:19]

    out.product_name               = os.path.basename(outname)

    out.info                       = 'ONNS (OLCI Neural Network Swarm) is a multi-water algorithm, specially designed to retrieve water quality parameters from SENTINEL-3 OLCI satellite data. In theory, the algorithm is applicable for all natural waters, from clearest oceanic waters to very turbid coastal or highly absorbing waters. Fuzzy logic optical water type classification is applied in conjunction with a set of specific neural networks.'
    out.version                    = version
    out.version_release            = release

    out.originator                 = 'Martin Hieronymi'
    out.originator_contributer     = 'Dagmar Mueller, Wolfgang Schoenfeld, Helmut Schiller, Daniel Behr, Hajo Krasemann et al.'
    out.originator_institution     = 'Helmholtz-Zentrum Geesthacht, Germany'
    out.contact                    = 'martin.hieronymi@hzg.de'

    out.reference_1                = 'Hieronymi, M., Mueller, D., & Doerffer, R. (2017). The OLCI Neural Network Swarm (ONNS): A bio-geo-optical algorithm for open ocean and coastal waters. Frontiers in Marine Science, 4, 140. https://doi.org/10.3389/fmars.2017.00140'
    out.reference_2                = 'Hieronymi, M. (2019). Spectral band adaptation of ocean color sensors for applicability of the multi-water biogeo-optical algorithm ONNS. Optics Express, 27(12), A707-A724. https://doi.org/10.1364/OE.27.00A707'

    out.Data_conventions           = 'CF-1.6'
    out.crs                        = 'EPSG:4326'
#
#    out.metadata_profile           = 'beam'        # MH: Fake NETCDF4-BEAM Standard for python
#    out.metadata_version           = '0.5'

    out.output_size                = str(output_size)
    out.output_size_info           = 'Option for data output size: 0 = standard product output (12 products + uncertainty) (default), 1 = extended processor output (+ Rrs, total IOPs, Dominance, etc), 2 = excessive processor output incl. OWT details'

    out.band_adaptation            = str(adapt)
    out.band_adaptation_info       = 'Option for band shifting: 0 = no band adaptation (default), 1 = only band 400nm is adapted (replaced), 2 = all bands are adapted (replaced) from input'

    
    

    ### 
    # Save all masks and L1 and L2 information
    
    out.createDimension('x', valid.shape[0])
    out.createDimension('y', valid.shape[1])
        
    
    test        = out.createVariable('longitude', 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)       
    test[:,:]   = lon[:,:]
    
    test.units              = 'degrees_east'
    test.standard_name      = 'longitude' 
    test.long_name          = 'Longitude in degrees' 
    test.coordinates        = 'lat lon' 
        
    
    test        = out.createVariable('latitude', 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
    test[:,:]   = lat[:,:]
    
    test.units              = 'degrees_north'
    test.standard_name      = 'latitude' 
    test.long_name          = 'Latitude in degrees' 
    test.coordinates        = 'lat lon' 
    
    
    test        = out.createVariable('ONNS_water', 'b', ('x', 'y'), zlib = True)
    test[:,:]   = valid[:,:]
    
    test.units              = '1'
    test.standard_name      = 'ONNS_water' 
    test.long_name          = 'Level_2 mask with non-land and non-cloud pixel that are calculated with ONNS' 
    test.coordinates        = 'lat lon' 

    
    test        = out.createVariable('land', 'b', ('x', 'y'), zlib = True)
    test[:,:]   = land[:,:]
    
    test.units              = '1'
    test.standard_name      = 'land' 
    test.long_name          = 'Level_1 land mask' 
    test.coordinates        = 'lat lon' 
    
    
    test        = out.createVariable('cloud', 'b', ('x', 'y'), zlib = True)
    test[:,:]   = cloud[:,:]
    
    test.units              = '1'
    test.standard_name      = 'cloud' 
    test.long_name          = 'Level_1 cloud mask' 
    test.coordinates        = 'lat lon' 



    ### 
    # Save all masks and L1 and L2 information
    
    if (output_size > 0):
    
        test        = out.createVariable('AC_flag_negative_reflectance', 'b', ('x', 'y'), zlib = True)
        test[:,:]   = flag_negative[:,:]
        
        test.units              = '1'
        test.standard_name      = 'AC_flag_negative_reflectance' 
        test.long_name          = 'Level_2 flag for implausible AC output. It applies if any value from the remote sensing reflectance spectrum, which is delivered by the atmospheric correction, is negative.' 
        test.coordinates        = 'lat lon' 
        
        
        test        = out.createVariable('AC_flag_suspect_pixel', 'b', ('x', 'y'), zlib = True)
        test[:,:]   = flag_suspect[:,:]
        
        test.units              = '1'
        test.standard_name      = 'AC_flag_suspect_pixel' 
        test.long_name          = 'Level_2 flag for implausible AC output. It applies if any value from the remote sensing reflectance spectrum, which is delivered by the atmospheric correction, is above 10.' 
        test.coordinates        = 'lat lon' 
            
        
        test        = out.createVariable('OWT_flag_not_classifiable', 'b', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_nonclassify
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'OWT_flag_not_classifiable' 
        test.long_name          = 'Level_2 flag for non-classifiable reflectance spectrum. It applies if the fuzzy logic optical water type (OWT) classification cannot attribute weights above 0.0001 to any OWT.' 
        test.coordinates        = 'lat lon' 
    
        
        test        = out.createVariable('OWT_flag_insufficient_memberships', 'b', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_lowmember_01
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'OWT_flag_insufficient_memberships' 
        test.long_name          = 'Level_2 flag for insufficient memberships in optical water types (OWT). It applies if the fuzzy logic OWT classification cannot attribute weights above 0.1 to any OWT.' 
        test.coordinates        = 'lat lon'     
        
        
        test        = out.createVariable('OWT_flag_low_memberships', 'b', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_lowmember_03
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'OWT_flag_low_memberships' 
        test.long_name          = 'Level_2 flag for low memberships in optical water types (OWT). It applies if the fuzzy logic OWT classification cannot attribute weights above 0.3 to any OWT.' 
        test.coordinates        = 'lat lon'     
    
        
        test        = out.createVariable('OWT_flag_low_max_memberships', 'b', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_lowmember_05
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'OWT_flag_low_max_memberships' 
        test.long_name          = 'Level_2 flag for non-dominant optical water types (OWT). It applies if the fuzzy logic OWT classification cannot find a dominant OWT and only attributes weights below 0.5 to single OWTs.' 
        test.coordinates        = 'lat lon'     
    
        
        test        = out.createVariable('ONNS_valid', 'b', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_ONNS_valid
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'ONNS_valid' 
        test.long_name          = 'Level_2 mask that shows where ONNS in-water products are valid. It applies if the fuzzy logic OWT classification attributes high weights.' 
        test.coordinates        = 'lat lon'     
    
            
        test        = out.createVariable('Band_adapter_fail', 'b', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_adapter_fail
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'Band_adapter_fail' 
        test.long_name          = 'Level_2 flag for failure of band adapter NN.' 
        test.coordinates        = 'lat lon'     
        
        
        test        = out.createVariable('flag_Case_bNN', 'i1', ('x', 'y'), zlib = True)
        b           = np.zeros(valid.shape)
        b[valid]    = flag_Case_bNN
        test[:,:]   = b 
        
        test.units              = '1'
        test.standard_name      = 'flag_Case_bNN' 
        test.long_name          = 'Level_2 flag for application of background NNs for merged OC products in case of low OWT total memberships (of < 0.3). 0 = OWT classification valid. 1 = "Case-1 water" background NN applied. 2 = "Case-2 water" background NN applied.' 
        test.coordinates        = 'lat lon'     
    


        ### 
        # Save all related to optical water type classification 
    
        test        = out.createVariable('OWT_max_membership', 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
        
        b           = np.zeros(valid.shape)
        b[valid]    = maxMemb
        b[~valid]   = np.nan
        
        test[:,:]   = b
        
        test.units              = '1'
        test.standard_name      = 'OWT_max_membership' 
        test.long_name          = 'Shows the optical water type (OWT) with maximum membership. The applied fuzzy logic OWT classification distinguishes between 13 OWTs.' 
        test.coordinates        = 'lat lon'         
        
        
        
        test        = out.createVariable('OWT_total_membership', 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
        
        b           = np.zeros(valid.shape)
        b[valid]    = total_membership
        b[~valid]   = np.nan
        
        test[:,:]   = b
        
        test.units              = '1'
        test.standard_name      = 'OWT_total_membership' 
        test.long_name          = 'Shows the total membership of all optical water types (OWT). The applied fuzzy logic OWT classification distinguishes between 13 OWTs.' 
        test.coordinates        = 'lat lon'     
        
        
        if (output_size == 2):
    
            for N in range(1, 14):      # 1 to 13 
             
                if N < 10:
                    test            = out.createVariable('OWT_original_weights_0' + str(N), 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
                    test2           = out.createVariable('OWT_proportional_weights_0' + str(N), 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
                else: 
                    test            = out.createVariable('OWT_original_weights_' + str(N), 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
                    test2           = out.createVariable('OWT_proportional_weights_' + str(N), 'f4', ('x', 'y'), zlib = True, fill_value = np.nan)
                
                b           = np.zeros(valid.shape)
                b[valid]    = m[:, N-1]
                b[~valid]   = np.nan
                test[:,:]   = b[:,:]
                
                test.units              = '1'
                test.standard_name      = 'OWT_original_weights' 
                test.long_name          = 'Original weights per optical water type (OWT) from fuzzy logic classification. ' 
                test.coordinates        = 'lat lon'         
                
                
                b           = np.zeros(valid.shape)
                b[valid]    = m2[:, N-1]
                b[~valid]   = np.nan
                test2[:,:]  = b[:,:]
                
                test2.units             = '1'
                test2.standard_name     = 'OWT_proportional_weights' 
                test2.long_name         = 'Portion of weights per optical water type (OWT) relative to the total memberships. ' 
                test2.coordinates       = 'lat lon'         
            
        
        
        
    ### 
    # Save all ONNS products 
        
    # All ONNS outputs - also CDOM and a_g_440 
    Variables_1     = ['Chl_ONNS', 'CDOM_ONNS', 'ISM_ONNS', 'a_g_440_ONNS', 'a_p_440_ONNS', 'a_m_440_ONNS', 'b_p_440_ONNS', 'b_m_440_ONNS', 'FU_ONNS', 'K_d_490_ONNS', 'K_u_490_ONNS', 'a_dg_412_ONNS', 'b_bp_510_ONNS']    
    Variables_bNN   = ['Chl_ONNS_bNN', 'CDOM_ONNS_bNN', 'ISM_ONNS_bNN', 'a_g_440_ONNS_bNN', 'a_p_440_ONNS_bNN', 'a_m_440_ONNS_bNN', 'b_p_440_ONNS_bNN', 'b_m_440_ONNS_bNN', 'FU_ONNS_bNN', 'K_d_490_ONNS_bNN', 'K_u_490_ONNS_bNN', 'a_dg_412_ONNS_bNN', 'b_bp_510_ONNS_bNN']    
    Variables_OWT   = ['Chl_ONNS_OWT', 'CDOM_ONNS_OWT', 'ISM_ONNS_OWT', 'a_g_440_ONNS_OWT', 'a_p_440_ONNS_OWT', 'a_m_440_ONNS_OWT', 'b_p_440_ONNS_OWT', 'b_m_440_ONNS_OWT', 'FU_ONNS_OWT', 'K_d_490_ONNS_OWT', 'K_u_490_ONNS_OWT', 'a_dg_412_ONNS_OWT', 'b_bp_510_ONNS_OWT']    
    Units_1         = ['mg.m-3', 'm-1', 'g.m-3',  'm-1', 'm-1', 'm-1', 'm-1', 'm-1', '1', 'm-1', 'm-1', 'm-1', 'm-1']
    Dscr_1          = ['(ONNS) Algal (chlorophyll) pigment concentration', '(ONNS) CDOM absorption coefficient at 440 nm (from concentration nets)', '(ONNS) Concentration of inorganic suspended matter', '(ONNS) CDOM absorption coefficient at 440 nm (from IOP nets)', '(ONNS) Absorption coefficient of phytoplankton particles at 440 nm', '(ONNS) Absorption coefficient of minerals at 440 nm', '(ONNS) Scattering coefficient of phytoplankton particles at 440 nm', '(ONNS) Scattering coefficient of minerals at 440 nm', '(ONNS) Forel-Ule number', '(ONNS) Downwelling diffuse attenuation coefficient at 490 nm', '(ONNS) Upwelling diffuse attenuation coefficient at 490 nm', '(ONNS) Absorption coefficient of detritus plus CDOM at 412 nm', '(ONNS) Total back-scattering coefficient of all particles at 510 nm']


        
    for i in range(len(Variables_1)):
        
        if (output_size == 2):
            
            test            = out.createVariable(Variables_OWT[i], 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
            a               = total_out_weighted[:,i]
            b               = np.zeros(valid.shape)
            b[valid]        = a
            b[~valid]       = np.nan
            
            test[:,:]       = b
            
            test.units              = Units_1[i]
            test.standard_name      = Variables_1[i]
            test.long_name          = Dscr_1[i]
            test.coordinates        = 'lat lon'         
            
            
            
            test            = out.createVariable(Variables_bNN[i], 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
            a               = total_out_bNN[:,i]
            b               = np.zeros(valid.shape)
            b[valid]        = a
            b[~valid]       = np.nan
            
            test[:,:]       = b
            
            test.units              = Units_1[i]
            test.standard_name      = Variables_1[i]
            test.long_name          = Dscr_1[i]
            test.coordinates        = 'lat lon'         
            
        
        
        test            = out.createVariable(Variables_1[i], 'f4', ('x','y'), zlib = True, fill_value = np.nan)

        a               = total_out_merged[:,i]
        b               = np.zeros(valid.shape)
        b[valid]        = a
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = Units_1[i]
        test.standard_name      = Variables_1[i]
        test.long_name          = Dscr_1[i]
        test.coordinates        = 'lat lon'         
        
        

    
    ###     
    # Save variables for uncertainty, where only a_g_440 is used 
    Variables_2 = ['Chl_ONNS_uncertainty', 'ISM_ONNS_uncertainty', 'a_g_440_ONNS_uncertainty', 'a_p_440_ONNS_uncertainty', 'a_m_440_ONNS_uncertainty', 'b_p_440_ONNS_uncertainty', 'b_m_440_ONNS_uncertainty', 'FU_ONNS_uncertainty', 'K_d_490_ONNS_uncertainty', 'K_u_490_ONNS_uncertainty', 'a_dg_412_ONNS_uncertainty', 'b_bp_510_ONNS_uncertainty'] 
    Dscr_2      = ['(ONNS) Error estimate for algal (chlorophyll) pigment concentration', '(ONNS) Error estimate for concentration of inorganic suspended matter', '(ONNS) Error estimate for CDOM absorption coefficient at 440 nm (from IOP nets)', '(ONNS) Error estimate for absorption coefficient of phytoplankton particles at 440 nm', '(ONNS) Error estimate for absorption coefficient of minerals at 440 nm', '(ONNS) Error estimate for scattering coefficient of phytoplankton particles at 440 nm', '(ONNS) Error estimate for scattering coefficient of minerals at 440 nm', '(ONNS) Error estimate for Forel-Ule number', '(ONNS) Error estimate for downwelling diffuse attenuation coefficient at 490 nm', '(ONNS) Error estimate for upwelling diffuse attenuation coefficient at 490 nm', '(ONNS) Error estimate for absorption coefficient of detritus plus CDOM at 412 nm', '(ONNS) Error estimate for total back-scattering coefficient of all particles at 510 nm']


    for i in range(len(Variables_2)):
        
        test            = out.createVariable(Variables_2[i], 'f4', ('x','y'), zlib = True, fill_value = np.nan)
        
        a               = total_BIAS_out_weighted[:,i]
        b               = np.zeros(valid.shape)
        b[valid]        = a
        b[~valid]       = np.nan
        
        test[:,:]       = b

        test.units              = 'percent'
        test.standard_name      = Variables_2[i]
        test.long_name          = Dscr_2[i]
        test.coordinates        = 'lat lon'         
        
        
        
    if (output_size > 0):
                        
        ###
        # Save all atmospheric corrected remote sensing reflectances at ONNS bands 
                            
        Variables_3     = ['Rrs_400', 'Rrs_412', 'Rrs_442', 'Rrs_490', 'Rrs_510', 'Rrs_560', 'Rrs_620', 'Rrs_665', 'Rrs_754', 'Rrs_779', 'Rrs_865']
        lambda_ONNS     = [400.0, 412.5, 442.5, 490.0, 510.0, 560.0, 620.0, 665.0, 755.0, 777.5, 865.0]
        
        
        for i in range(0, 11):
            
            test            = out.createVariable(Variables_3[i], 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
            b               = np.zeros(valid.shape)
            b[valid]        = Rrs_ONNS[:, i]
            b[~valid]       = np.nan
            test[:,:]       = b[:,:]
            
            test.units              = 'sr-1'
            test.standard_name      = Variables_3[i] 
            test.long_name          = 'Remote-sensing reflectance Rrs delivered by the atmospheric correction' 
            test.coordinates        = 'lat lon' 
            test.wavelength         = lambda_ONNS[i]                            # MH: to specify "Spectral Wavelength" (not working in SNAP)
                    

        
        test            = out.createVariable('lambda_Rrs_max', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
        
        b               = np.zeros(valid.shape)
        b[valid]        = lambda_Rrs_max
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = 'nm'
        test.standard_name      = 'lambda_Rrs_max' 
        test.long_name          = 'Wavelength of maximum remote-sensing reflectance (ONNS uses 11 out of 21 OLCI bands)' 
        test.coordinates        = 'lat lon'     

        
            
        ### 
        # New product for total absorption and scattering at 440 nm 
            
        aw_440_20deg_30psu  = 0.0064000                                         # MH: water absorption coefficient at 440 nm from Seawater_ab_T20_S30_2015.txt
        bw_440_20deg_30psu  = 0.0042557                                         # MH: corresponding scattering coefficient 
        
        atot            = np.zeros((total_out_merged.shape[0]))
        
        test            = out.createVariable('a_tot_440_ONNS', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
        atot            = total_out_merged[:,3] + total_out_merged[:,4] + total_out_merged[:,5] + aw_440_20deg_30psu    # MH: a_cdom + a_p + a_m + a_w
        b               = np.zeros(valid.shape)
        b[valid]        = atot
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = 'm-1'
        test.standard_name      = 'a_tot_440_ONNS'
        test.long_name          = '(ONNS) Total absorption coefficient at 440 nm, including CDOM, phytoplankton, minerals, and water (0.0064 m-1 at 20degC/30PSU)'
        test.coordinates        = 'lat lon'             
            
            
            
        a               = np.zeros((total_out_merged.shape[0]))
        
        test            = out.createVariable('b_tot_440_ONNS', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
        a               = total_out_merged[:,6] + total_out_merged[:,7] + bw_440_20deg_30psu        # MH: b_p + b_m + b_w
        b               = np.zeros(valid.shape)
        b[valid]        = a
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = 'm-1'
        test.standard_name      = 'b_tot_440_ONNS'
        test.long_name          = '(ONNS) Total scattering coefficient at 440 nm, including phytoplankton, minerals, and water (0.0042557 m-1 at 20degC/30PSU)'
        test.coordinates        = 'lat lon'             
            
            
            
        ### 
        # New product for optical diminance at 440 nm - revised 20181205! 
            
        a           = total_out_merged[:,3] + total_out_merged[:,4] + total_out_merged[:,5]     # MH: a_tot without water 
        
        h1          = total_out_merged[:,4] / a                                 # MH: a_p / a_tot
        h2          = total_out_merged[:,3] / a                                 # MH: a_cdom / a_tot
        h3          = total_out_merged[:,5] / a                                 # MH: a_m / a_tot
        
        
        
        Dominance       = np.zeros((total_out_merged.shape[0]))                     # MH: all are zero (mixed) first, than allocation
        
        for i in range(Dominance.shape[0]):
            
            if (h1[i] > 0.5):
                
                Dominance[i]    = 1                                             # MH: phytoplankton-dominated absorption at 440 nm 
                
            elif (h2[i] > 0.5):
                
                Dominance[i]     = 2                                            # MH: CDOM-dominated absorption at 440 nm 
                                                        
            elif (h3[i] > 0.5):
                                                        
                Dominance[i]     = 3                                            # MH: sediment-dominated absorption at 440 nm 
    
    
    
        test            = out.createVariable('Optical_dominance_ONNS', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
        #b          = np.zeros(valid.shape)
        b[valid]        = Dominance
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = '-'
        test.standard_name      = 'Optical_dominance_ONNS'
        test.long_name          = '(ONNS) Dominance of water constituents in terms of the absorption coefficient at 440 nm (without water absorption, which is 0.0064 m-1 at 20degC/30PSU). 0 = mixed, 1 = phytoplankton-dominated absorption, 2 = CDOM-dominated absorption, 3 = sediment-dominated absorption.'
        test.coordinates        = 'lat lon'         
    


        ### 
        # New product for POC 20181205! 

        # a               = np.zeros((total_out_merged.shape[0]))
        #
        # test            = out.createVariable('POC_TSM_1', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
        #
        # a               = 0.1* (total_out_merged[:,6] + total_out_merged[:,7])  # MH: 0.1* (b_p + b_m) according RR
        # b               = np.zeros(valid.shape)
        # b[valid]        = a
        # b[~valid]       = np.nan
        #
        # test[:,:]       = b
        #
        # test.units              = 'g.m-3'
        # test.standard_name      = 'POC_TSM_1'
        # test.long_name          = '(ONNS) Particulate organic carbon (POC) related to TSM and particulate scattering coefficient at 440 nm (including phytoplankton and minerals). According HZG in situ data --> POC_TSM_1 = 0.1* (bp440 + bm440) '
        # test.coordinates        = 'lat lon'
        #
        #
        # a               = np.zeros((total_out_merged.shape[0]))
        #
        # test            = out.createVariable('POC_TSM_2', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
        #
        # a               = 5.5* total_out_merged[:,12]                           # MH: 5.5* (bbp510) according RR fits best
        # b               = np.zeros(valid.shape)
        # b[valid]        = a
        # b[~valid]       = np.nan
        #
        # test[:,:]       = b
        #
        # test.units              = 'g.m-3'
        # test.standard_name      = 'POC_TSM_2'
        # test.long_name          = '(ONNS) Particulate organic carbon (POC) related to TSM and particulate backscattering coefficient at 510 nm (including phytoplankton and minerals). According HZG in situ data --> POC_TSM_2 = 5.5* bbp510  (better correlation than POC_TSM_1)'
        # test.coordinates        = 'lat lon'
        #
        #
        # a               = np.zeros((total_out_merged.shape[0]))
        #
        # test            = out.createVariable('POC_Phy_1', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
        #
        # a               = 2.7* total_out_merged[:,4]                            # MH: 2.7* ap440 according RR
        # b               = np.zeros(valid.shape)
        # b[valid]        = a
        # b[~valid]       = np.nan
        #
        # test[:,:]       = b
        #
        # test.units              = 'g.m-3'
        # test.standard_name      = 'POC_Phy_1'
        # test.long_name          = '(ONNS) Particulate organic carbon (POC) related to Phytoplankton and pigment absorption coefficient at 440 nm. According HZG in situ data --> POC_Phy_1 = 2.7* ap440  '
        # test.coordinates        = 'lat lon'
        #
        #
        # a               = np.zeros((total_out_merged.shape[0]))
        #
        # test            = out.createVariable('POC_Phy_2', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
        #
        # a               = 2.3* (total_out_merged[:,4] + total_out_merged[:,5])  # MH: 2.3* (ap440 + am440) according RR
        # b               = np.zeros(valid.shape)
        # b[valid]        = a
        # b[~valid]       = np.nan
        #
        # test[:,:]       = b
        #
        # test.units              = 'g.m-3'
        # test.standard_name      = 'POC_Phy_2'
        # test.long_name          = '(ONNS) Particulate organic carbon (POC) related to Phytoplankton and total particulate absorption coefficient at 440 nm (including phytoplankton and minerals). According HZG in situ data --> POC_Phy_2 = 2.3* (ap440 + am440) '
        # test.coordinates        = 'lat lon'
        #
        
        a               = np.zeros((total_out_merged.shape[0]))
        
        test            = out.createVariable('POC', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
        a               = 5.5* total_out_merged[:,12] + 2.7* total_out_merged[:,4] # MH:  5.5* bbp510 + 2.7* ap440 according RR best and phyiscal fit  
        b               = np.zeros(valid.shape)
        b[valid]        = a
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = 'g.m-3'
        test.standard_name      = 'POC'
        test.long_name          = '(ONNS) Total particulate organic carbon (POC) related to Phytoplankton and TSM. POC = POC_TSM_2 + POC_Phy_1. According HZG in situ data --> POC = 5.5* bbp510 + 2.7* ap440 '
        test.coordinates        = 'lat lon'             
            
        
        
        ### 
        # New product for DOC 20181205! 
        
        a               = np.zeros((total_out_merged.shape[0]))
        
        test            = out.createVariable('DOC', 'f4', ('x','y'), zlib = True, fill_value = np.nan)
            
        a               = 10**2.525 * total_out_merged[:,3]**0.659              # MH:  10**2.525* ag440**0.659 according Juhls et al. (2019)  
        b               = np.zeros(valid.shape)
        b[valid]        = a
        b[~valid]       = np.nan
        
        test[:,:]       = b
        
        test.units              = 'mg.m-3'
        test.standard_name      = 'DOC'
        test.long_name          = '(ONNS) Dissolved organic carbon (DOC) related to CDOM absorption at 440 nm. According Juhls et al. (2019) -->  DOC = 10**2.525* ag440**0.659 '
        test.coordinates        = 'lat lon'             
            
                
        

    # Close the one output file 
    out.close()
    


#def save_results_txt(outname, outname_1, maxMemb, m, m2, total_membership, total_out_weighted, total_out_weighted_with_Unc, total_out_bNN, total_out_merged, total_BIAS_out_weighted, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid, Rrs_ONNS, flag_Case_bNN, version, output_size, lambda_Rrs_max, P_ID):
def save_results_txt(outname, outname_1, outname_2, outname_3, maxMemb, m, m2, total_membership, total_out_weighted, total_out_bNN, total_out_merged, total_BIAS_out_weighted, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid, Rrs_ONNS, flag_Case_bNN, version, output_size, lambda_Rrs_max, P_ID):
   
    ###
    # One file with ONNS products - reduced or full output
    
    f           = open(outname, 'a')
    
    if (output_size == 0):
        
        Header          = ['%      P_ID    Chl_ONNS   CDOM_ONNS    ISM_ONNS  ag440_ONNS  ap440_ONNS  am440_ONNS  bp440_ONNS  bm440_ONNS     FU_ONNS  Kd490_ONNS  Ku490_ONNS adg412_ONNS bbp510_ONNS']
    
        np.savetxt(f, X = Header, delimiter = '\t', fmt = '%s')
        
        data            = np.zeros((total_out_merged.shape[0], 14))
        
        for k in range(total_out_merged.shape[0]):
            
            data[k, 0]      = P_ID[k]
            data[k, 1:14]   = total_out_merged[k,:]
        
        data            = np.around(data, decimals = 3)
        
        np.savetxt(f, X = data, delimiter = '\t', fmt = '%11.0f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.0f %11.3f %11.3f %11.3f %11.3f')
        
        
    else:
        
        
        aw_440_20deg_30psu  = 0.0064000                                         # MH: water absorption coefficient at 440 nm from Seawater_ab_T20_S30_2015.txt
        bw_440_20deg_30psu  = 0.0042557                                         # MH: corresponding scattering coefficient 
        
        atot            = np.zeros((total_out_merged.shape[0]))
        atot            = total_out_merged[:,3] + total_out_merged[:,4] + total_out_merged[:,5] + aw_440_20deg_30psu    # MH: a_cdom + a_p + a_m + a_w
                
        btot            = np.zeros((total_out_merged.shape[0]))
        btot            = total_out_merged[:,6] + total_out_merged[:,7] + bw_440_20deg_30psu        # MH: b_p + b_m + b_w


        a               = total_out_merged[:,3] + total_out_merged[:,4] + total_out_merged[:,5]     # MH: a_tot without water 
        
        h1              = total_out_merged[:,4] / a                             # MH: a_p / a_tot
        h2              = total_out_merged[:,3] / a                             # MH: a_cdom / a_tot
        h3              = total_out_merged[:,5] / a                             # MH: a_m / a_tot
        
        Dominance       = np.zeros((total_out_merged.shape[0]))                 # MH: all are zero (mixed) first, than allocation
        
        for i in range(Dominance.shape[0]):
            
            if (h1[i] > 0.5):
                
                Dominance[i]    = 1                                             # MH: phytoplankton-dominated absorption at 440 nm 
                
            elif (h2[i] > 0.5):
                
                Dominance[i]     = 2                                            # MH: CDOM-dominated absorption at 440 nm 
                                                        
            elif (h3[i] > 0.5):
                                                        
                Dominance[i]     = 3                                            # MH: sediment-dominated absorption at 440 nm 
    

            
        Header          = ['%        ID    Chl_ONNS   CDOM_ONNS    ISM_ONNS  ag440_ONNS  ap440_ONNS  am440_ONNS  bp440_ONNS  bm440_ONNS     FU_ONNS  Kd490_ONNS  Ku490_ONNS adg412_ONNS bbp510_ONNS     atot440     btot440   dominance   POC_TSM_1   POC_TSM_2   POC_Phy_1   POC_Phy_2    POC_ONNS    DOC_ONNS     MaxMemb     Rrs_max']

        np.savetxt(f, X = Header,  fmt = '%s')
        
        data            = np.zeros((total_out_merged.shape[0], 25))
        
        for k in range(total_out_merged.shape[0]):
            
            data[k, 0]      = P_ID[k]
            data[k, 1:14]   = total_out_merged[k,:]
            data[k, 14]     = atot[k]
            data[k, 15]     = btot[k]
            data[k, 16]     = Dominance[k]
            data[k, 17]     = 0.1* (total_out_merged[k,6] + total_out_merged[k,7])      # MH: 0.1* (b_p + b_m) according RR
            data[k, 18]     = 5.5* total_out_merged[k,12]                               # MH: 5.5* (bbp510) according RR fits best  
            data[k, 19]     = 2.7* total_out_merged[k,4]                                # MH: 2.7* ap440 according RR 
            data[k, 20]     = 2.3* (total_out_merged[k,4] + total_out_merged[k,5])      # MH: 2.3* (ap440 + am440) according RR 
            data[k, 21]     = 5.5* total_out_merged[k,12] + 2.7* total_out_merged[k,4]  # MH:  5.5* bbp510 + 2.7* ap440 according RR best and phyiscal fit  
            data[k, 22]     = 10**2.532 * total_out_merged[k,3]**0.622                  # MH:  10**2.532* ag440**0.622 according Juhls et al. (in prep)  
            data[k, 23]     = maxMemb[k]
            data[k, 24]     = lambda_Rrs_max[k]
        
        
        data            = np.around(data, decimals = 3)
        
        np.savetxt(f, X = data, delimiter = '\t', fmt = '%11.0f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.0f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.0f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.0f %11.1f')
        
        
    f.close()
        
    
    
    ###
    # One file with product uncertainties --> maybe NaN because not applied to merged ONNS products, only from OWT classification
    
    f           = open(outname_1, 'a')
    
    Header      = ['%        ID   UChl_ONNS   UISM_ONNS Uag440_ONNS Uap440_ONNS Uam440_ONNS Ubp440_ONNS Ubm440_ONNS    UFU_ONNS UKd490_ONNS UKu490_ONNS Uad412_ONNS Ubb510_ONNS']
    
    np.savetxt(f, X = Header, delimiter = '\t', fmt = '%s')
    
    data        = np.zeros((total_out_merged.shape[0], 13))
    
    for k in range(total_out_merged.shape[0]):
        
        data[k, 0]      = P_ID[k]
        data[k, 1:13]   = total_BIAS_out_weighted[k,:]
#        data[k, 1:13]   = total_out_weighted_with_Unc[k,:]

    data        = np.around(data, decimals = 3)
    
    np.savetxt(f, X = data, delimiter = '\t', fmt = '%11.0f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f %11.3f')
    
    f.close()

    
    ###
    # One file with OLCI Rrs --> maybe results from band adapter 
    
    if (output_size > 0):
        
        f           = open(outname_2, 'a')
        
        Header      = ['%        ID      Rrs400      Rrs412      Rrs443      Rrs490      Rrs510      Rrs560      Rrs620      Rrs665      Rrs755      Rrs778      Rrs865']
        
        np.savetxt(f, X = Header, delimiter = '\t', fmt = '%s')
        
        data        = np.zeros((Rrs_ONNS.shape[0], 12))
        
        for k in range(Rrs_ONNS.shape[0]):
            
            data[k, 0]      = P_ID[k]
            data[k, 1:12]   = Rrs_ONNS[k,:]
    
        #data        = np.around(data, decimals = 7)
        
        np.savetxt(f, X = data, delimiter = '\t', fmt = '%11.0f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f')
        
        f.close()

 

    ###
    # One file with OWT memberships  
    
    if (output_size == 2):
        
        f           = open(outname_3, 'a')
        
        Header      = ['%        ID      Rrs400      Rrs412      Rrs443      Rrs490      Rrs510      Rrs560      Rrs620      Rrs665      Rrs755      Rrs778      Rrs865']
        Header      = ['%        ID       OWT01       OWT02       OWT03       OWT04       OWT05       OWT06       OWT07       OWT08       OWT09       OWT10       OWT11       OWT12       OWT13']
        
        np.savetxt(f, X = Header, delimiter = '\t', fmt = '%s')
        
        data        = np.zeros((m.shape[0], 14))
        
        for k in range(m.shape[0]):
            
            data[k, 0]      = P_ID[k]
            data[k, 1:14]   = m[k,:]
    
        #data        = np.around(data, decimals = 7)
        
        np.savetxt(f, X = data, delimiter = '\t', fmt = '%11.0f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f')
        
        f.close()

 


### -------------------------------------------------------------------
# MAIN
### -------------------------------------------------------------------

if __name__=='__main__':

    #print('Usage: ')
    #exit(0)

    start_time          = dt.now()
    
    # Command line parsing

    parser              = argparse.ArgumentParser(description = 'ONNS (OLCI Neural Network Swarm) processor')
    
    parser.add_argument('iprod', action = 'store', help = 'Input InSitu/C2RCC/Polymer/IPF/FUB L2 reflectance product')
    parser.add_argument('-od', '--outdir', action = 'store', help = 'Output directory, default current directory')
    parser.add_argument('-ofile', '--outfile', action = 'store', help = 'Define name of output file')
    parser.add_argument('-sensor', action = 'store', help = 'Define used sensor - currently atmospheric corrected data processing of: "OLCI" (default; C2R, Pol, IPF, FUB), "MERIS" (Pol), "VIIRS" (Pol), or "MODIS" (Pol); alternatively in situ data (.txt) at wavelengths of: "EnMAP", "GOCI2", "OCM2", "PACE", "SeaWiFS", "SeaWiFS_OCCCI", or "SGLI"')
    parser.add_argument('-adapt', action = 'store', help = 'Option for band adaptation: 0 = no band adaptation (default), 1 = only band 400nm is adapted (replaced), 2 = all bands are adapted (replaced) from MERIS input')
    parser.add_argument('-ac', action = 'store', help = 'Define used atmospheric correction: 0 = InSitu (no AC applied, txt data), 1 = C2R (default), 2 = POLYMER, 3 = IPF, 4 = FUB')
    parser.add_argument('-osize', action = 'store', help = 'Define output size: 0 = standard product output (12 products + uncertainty) (default), 1 = extended processor output (+ Rrs, total IOPs, Dominance, etc), 2 = excessive processor output incl. OWT details') 
    parser.add_argument('-txt_header', action = 'store', help = 'For in situ data (txt format): 0 = no header, 1 = header line (default), n = number of header lines') 
    parser.add_argument('-txt_ID', action = 'store', help = 'For in situ data (txt format): 0 = no line IDs (e.g. station number), 1 = first column with ID (default)') 
    parser.add_argument('-txt_columns', '--list', nargs = '+', action = 'store', help = 'For in situ data (txt format) and depending on sensor: Specification of used columns, e.g. [0, 1, 2, 3, 4, 5, 6, 7, 11, 15, 16] = columns of OLCI bands used for ONNS', required = True)
    
    
    args                = parser.parse_args()
    
    path_to_classes     = os.path.join(sdir, 'classification', 'preselect_reducedHL_20161006H1203')
    class_name          = os.path.basename(path_to_classes)
    path_to_NN          = os.path.join(sdir, 'nets')
    
    inpath              = os.path.dirname(args.iprod)
    infile              = os.path.basename(args.iprod)
    
    
    if args.outdir and os.path.isdir(args.outdir):
        outpath         = args.outdir   
    else:
        outpath         = os.getcwd()
    
    
    # Output size 
    
    if args.osize == '0':
        output_size     = 0                                                     # MH: standard product output (12 products + uncertainty)
    elif args.osize == '1':
        output_size     = 1                                                     # MH: extended processor output (+ Rrs, total IOPs, Dominance, etc)
    elif args.osize == '2':
        output_size     = 2                                                     # MH: full processor output incl. OWT details
    else:
        print('Error: Define "-osize" output size: 0 = standard product output (12 products + uncertainty) (default), 1 = extended processor output (+ Rrs, total IOPs, Dominance, etc), 2 = excessive processor output incl. OWT details') 
        sys.exit()
    

    
    # Used sensor (sensor bands) for AC and band adaptation
    
    if args.sensor == 'OLCI':
        
        # Sensor specification and if band adaptation is necessary 
        
        sensor          = 'OLCI'
        
        if args.adapt == '1':                                                       # MH: only band 400nm is adapted (replaced)
            
            adapt           = 1
            version         = ('_' + version + '_adapt_band_1')
            
        elif args.adapt == '2':                                                     # MH: all bands are adapted (replaced) from MERIS input
            
            adapt           = 2
            version         = ('_' + version + '_adapt_band_all')
            
        else:
            
            adapt           = 0                                                     # MH: no band adaptation        
            version         = ('_' + version)
            
        
            
        if args.ac == '1':          # C2R 
            ac              = 1            
        elif args.ac == '2':        # POLYMER 
            ac              = 2
        elif args.ac == '3':        # IPF 
            ac              = 3        
        elif args.ac == '4':        # FUB  
            ac              = 4            
            
        
        # Generation of the output file name
        
        if args.outfile or args.ac == '0':                                                            # MH: if output file name is provided... 
            
            if args.outfile: 
                outfile         = args.outfile
            else:
                outfile         = infile
            
            if outfile[-3:] == '.nc':
                print('Output file is NETCDF4 file.')
                outname         = os.path.join(outpath, outfile)
                
            elif outfile[-4:] == '.txt':
                print('Output file is a text file.')
                outname         = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_' + str(output_size) + '.txt')
                outname_1       = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_uncertainty_' + str(output_size) + '.txt')
                outname_2       = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_Rrs_' + str(output_size) + '.txt')
                outname_3       = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_OWTmemberships_' + str(output_size) + '.txt')

            else:
                print('Error: Output file must be NETCDF4 (.nc) or text (.txt) file.')
                #sys.exit()
                
            if inpath[-1] != '/':
                inpath          = os.path.join(inpath + '/')
            
            
            
        elif infile[7] == '1':                                                      # MH: Check if filename includes Level-1 OLCI data      
            
            outfile         = list(infile)
            outfile[7]      = '2'                                                   # MH: The product will be Level-2 
            
            if args.ac == '1':          # C2R 
                outfile[14]     = 'O'
            elif args.ac == '2':        # POLYMER 
                outfile[14]     = 'O'
            elif args.ac == '3':        # IPF 
                
                print('Error: Provide atmospheric corrected (Level-2) or in situ reflectance data at OLCI bands (C2R, POL, IPF, FUB or txt). ')
                print('Error: In case of IPF baseline corrected data, provide directory with .nc data, i.e. ".SEN3" directory ')
                sys.exit()
                
                #ac              = 3
                #outfile[14]     = 'O'

            elif args.ac == '4':        # FUB  
                outfile[14]     = 'O'
            else:                
                print('Error: Input file seems to be OLCI Level-1. Thus, "-ac" must be 3 for IPF.')
                #sys.exit()
                
            outfile         = ''.join(outfile)
            
            outname         = os.path.join(outpath, outfile[:-3] + '_' + str(output_size) + str(version) + '.nc')
                
                
        elif infile[7] == '2':
            
            outfile         = list(infile)
            
            if args.ac == '1':          # C2R 
                outfile[14]     = 'O'
            elif args.ac == '2':        # POLYMER 
                outfile[14]     = 'O'
            elif args.ac == '3':        # IPF 
                test            = infile.find('.SEN3')
                
                if test > -1:
                    
                    inpath          = os.path.join(inpath, infile)                    
                    infile          = infile[:test]
                    outfile         = list(infile)
                    outfile[14]     = 'O'
                    
                else:
            
                    print('Error: Provide atmospheric corrected (Level-2) or in situ reflectance data at OLCI bands (C2R, POL, IPF, FUB or txt) ')
                    print('Error: In case of IPF baseline corrected data, provide directory with .nc data, i.e. ".SEN3" directory ')
                    sys.exit()
                    
                
            elif args.ac == '4':        # FUB  
                outfile[14]     = 'O'
            else:                
                print('Error: Input file seems to be OLCI Level-1. Thus, "-ac" must be 3 for IPF.')
                #sys.exit()
                
            outfile         = ''.join(outfile)
            
            outname         = os.path.join(outpath, outfile[:-3] + '_' + str(output_size) + str(version) + '.nc')
            
            
        else: 
            
            outfile         = infile
            
            outname         = os.path.join(outpath, outfile)
            
            print('Warning: Input file name is not according to OLCI convention.')
            
                        

            


    if args.sensor != 'OLCI':
        
        # So far, only Polymer AC output as input possible for: MERIS, MODIS, and VIIRS 
        # All other sensors via band adapters only input as text files 
        
        if args.sensor == 'MERIS':
            
            sensor          = 'MERIS'
            
            if args.adapt == '1':                                                       # MH: only band 400nm is adapted (replaced)
                adapt           = 1
                version         = ('_' + version + '_MERIS_adapt_band_1')

            elif args.adapt == '2':                                                     # MH: all bands are adapted (replaced) from MERIS input
                adapt           = 2
                version         = ('_' + version + '_MERIS_adapt_all_bands')
            else:
                adapt           = 0                                                     # MH: no band adaptation        
                               
        elif args.sensor == 'MODIS':
            sensor          = 'MODIS'
            adapt           = 2
            version         = ('_' + version + '_MODIS_adapt_all_bands')
            ac              = 2                                                         # # So far, only Polymer AC output as input possible for MODIS
        elif args.sensor == 'VIIRS':
            sensor          = 'VIIRS'
            adapt           = 2
            version         = ('_' + version + '_VIIRS_adapt_all_bands')
            ac              = 2                                                         # # So far, only Polymer AC output as input possible for VIIRS
        elif args.sensor == 'EnMAP':
            sensor          = 'EnMAP'
            adapt           = 2
            version         = ('_' + version + '_EnMAP_adapt_all_bands')
        elif args.sensor == 'GOCI2':
            sensor          = 'GOCI2'
            adapt           = 2
            version         = ('_' + version + '_GOCI2_adapt_all_bands')
        elif args.sensor == 'OCM2':
            sensor          = 'OCM2'
            adapt           = 2
            version         = ('_' + version + '_OCM2_adapt_all_bands')
        elif args.sensor == 'PACE':
            sensor          = 'PACE'
            adapt           = 2
            version         = ('_' + version + '_PACE_adapt_all_bands')
        elif args.sensor == 'SeaWiFS':
            sensor          = 'SeaWiFS'
            adapt           = 2
            version         = ('_' + version + '_SeaWiFS_adapt_all_bands')
        elif args.sensor == 'SeaWiFS_OCCCI':
            sensor          = 'SeaWiFS_OCCCI'
            adapt           = 2
            version         = ('_' + version + '_SeaWiFS_OCCCI_adapt_all_bands')
        elif args.sensor == 'SGLI':
            sensor          = 'SGLI'
            adapt           = 2
            version         = ('_' + version + '_SGLI_adapt_all_bands')
        else:
            print('Error: Unknown sensor')
            sys.exit()            


        if args.outfile:               
            outfile         = args.outfile            
        else:
            outfile         = infile
                       
            
        if outfile[-3:] == '.nc':
            print('Output file is NETCDF4 file.')
            outname         = os.path.join(outpath, outfile)
            
        elif outfile[-4:] == '.txt':
            print('Output file is a text file.')
            outname         = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_' + str(output_size) + '.txt')
            outname_1       = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_uncertainty_' + str(output_size) + '.txt')
            outname_2       = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_Rrs_' + str(output_size) + '.txt')
            outname_3       = os.path.join(outpath, outfile[:-4] + '_ONNS' + version + '_OWTmemberships_' + str(output_size) + '.txt')

        else:
            print('Error: Output file must be NETCDF4 (.nc) or text (.txt) file.')
            #sys.exit()
            
            
        if inpath[-1] != '/':
                inpath          = os.path.join(inpath + '/')
                

        
    # for in situ (txt format) data 
        
    if args.ac == '0':
        
        if args.list is not None:
            #print(args.list)
            txt_columns     = list(map(int, args.list))
        else:
            print('Error: Please provide -txt_columns --> a list with specification of used columns, e.g. 0 1 2 3 4 5 6 7 11 15 16 = columns of OLCI bands used for ONNS')
            
            
        if args.txt_ID is not None:
            #print(args.txt_ID)
            txt_ID          = int(args.txt_ID)
        else:
            print('Error: Please provide -txt_ID --> 0 = no line IDs (e.g. station number), 1 = first column with ID (default)')
            
            
        if args.txt_header is not None:
            #print(args.txt_header)
            txt_header      = int(args.txt_header)
        else:
            print('Error: Please provide -txt_header --> 0 = no header, 1 = header line (default), n = number of header lines')
            
            
        


    
    
    ### -------------------------------------------------------------------
   
    print('Start: ', str(dt.now()))
    print('Processing of: ', infile)     
    
    
    if args.ac == '0':          # MH: In situ data alternatively: 'txt' in infile.lower():
        
        Rrs_in, P_ID                            = prepare_processor_input_txt(inpath, infile, sensor, txt_ID, txt_columns, txt_header)
        
        Rrs_ONNS, flag_adapter_fail             = sensor_band_adapter(path_to_NN, Rrs_in, sensor, adapt)        

        m, m2, total_membership, maxMemb, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid     = classify_clustering_fuzzy(output_size, Rrs_ONNS, path_to_classes = path_to_classes)
            
        print('Approx. 15 % - ONNS application ...')    
        
        total_out_weighted, Chl_unweighted      = ONNS(path_to_NN, Rrs_ONNS, m2)
            
        print('Approx. 50 % - ONNS Background NN ...')
        
        total_out_bNN, Case, lambda_Rrs_max     = background_NN(path_to_NN, Rrs_ONNS)   
        
        print('Approx. 75 % - ONNS BIAS application ...')
        
        total_out_merged, flag_Case_bNN         = merge_products(total_membership, total_out_weighted, total_out_bNN, Case)

        total_BIAS_out_weighted                 = apply_BIAS_NN(path_to_NN, total_out_weighted, m2)
                
        save_results_txt(outname, outname_1, outname_2, outname_3, maxMemb, m, m2, total_membership, total_out_weighted, total_out_bNN, total_out_merged, total_BIAS_out_weighted, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid, Rrs_ONNS, flag_Case_bNN, version, output_size, lambda_Rrs_max, P_ID)

        
        
    else: 
    
            
        if (sensor == 'OLCI'):
            
            Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect  = prepare_processor_input(inpath, infile)
        
        elif (sensor == 'MERIS'):
            
            Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect  = prepare_processor_input_MERIS(inpath, infile)
            
        elif (sensor == 'MODIS'):
            
            Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect  = prepare_processor_input_MODIS(inpath, infile)
                           
        elif (sensor == 'VIIRS'):
            
            Rrs_in, valid, scene_in_rhow, lat, lon, cloud, land, AC, flag_negative, flag_suspect  = prepare_processor_input_VIIRS(inpath, infile)


        Rrs_ONNS, flag_adapter_fail             = sensor_band_adapter(path_to_NN, Rrs_in, sensor, adapt)
        
        m, m2, total_membership, maxMemb, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid     = classify_clustering_fuzzy(output_size, Rrs_ONNS, path_to_classes = path_to_classes)
            
        print('Approx. 15 % - ONNS application ...')    
        
        total_out_weighted, Chl_unweighted      = ONNS(path_to_NN, Rrs_ONNS, m2)
            
        print('Approx. 50 % - ONNS Background NN ...')
        
        total_out_bNN, Case, lambda_Rrs_max     = background_NN(path_to_NN, Rrs_ONNS)   
        
        print('Approx. 75 % - ONNS BIAS application ...')
               
        total_out_merged, flag_Case_bNN         = merge_products(total_membership, total_out_weighted, total_out_bNN, Case)

        total_BIAS_out_weighted                 = apply_BIAS_NN(path_to_NN, total_out_weighted, m2)
                
        save_results(outname, maxMemb, m, m2, total_membership, total_out_weighted, total_out_bNN, total_out_merged, total_BIAS_out_weighted, flag_nonclassify, flag_lowmember_01, flag_lowmember_03, flag_lowmember_05, flag_lowmember_09, flag_ONNS_valid, Rrs_ONNS, valid, flag_adapter_fail, flag_Case_bNN, version, output_size, lambda_Rrs_max)
    
    
    
    print('Ready ', str(dt.now()), ' after ', str(dt.now() - start_time))
















