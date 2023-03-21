import numpy as np
import os, sys, argparse
import pyproj

from netCDF4 import Dataset as nc
from datetime import datetime as dt
from fnmatch import filter
from osgeo import gdal

np.seterr(divide='ignore', invalid='ignore')  # MH: Ignore RuntimeWarnings

release             = '20221114'                                                # Date of release
version             = 'v01'                                                    # OCPFT Version

inpath_enmap = '/home/alvarado/projects/typsynsat/data/enpt/ENMAP01-____L2A-DT0000001567_20220709T105740Z_032_V010111_20230223T123718Z'
inpath = '/home/alvarado/projects/typsynsat/data/sentinel3/bodensee/2020/08/16'
infile = 'S3A_OL_1_EFR____20200816T095809_20200816T100109_20200816T120938_0179_061_350_2160_MAR_O_NR_002.SEN3.nc'

def enpt_rootdir(rootdir_l2b):
    """Check for EnPT L2B root directory."""
    if not os.path.isdir(rootdir_l2b):
        raise NotADirectoryError(rootdir_l2b, 'EnMAP images have to be provided as a directory'
                                              'containing all extracted files.')

    files = os.listdir(rootdir_l2b)

    if not files:
        raise RuntimeError("The root directory of the EnMAP L2B image %s is empty." % rootdir_l2b)

    matches = []
    for pattern in [
        '*-ACOUT_POLYMER_BITMASK.TIF',
        '*-ACOUT_POLYMER_LOGCHL.TIF'
    ]:

        matches.extend(filter(files, pattern))

        if not matches:
            raise FileNotFoundError('The root directory of the EnMAP L2B image %s misses a file with the pattern %s.'
                                    % (rootdir_l2b, pattern))
    return matches

def geo(inpath):
    # Check files to read from EnPT L2B root directory
    files = enpt_rootdir(inpath)

    if filter(files, '*_BITMASK.TIF')[0]:
        # open geottif bitmask
        ds_bitmask = gdal.Open(os.path.join(inpath, filter(files, '*_BITMASK.TIF')[0]))

    if filter(files, '*_LOGCHL.TIF')[0]:
        # open geottif logchl
        ds_logchl = gdal.Open(os.path.join(inpath, filter(files, '*_LOGCHL.TIF')[0]))

    # Get the geotransform parameters
    transform = ds_logchl.GetGeoTransform()

    # Get the size of the file
    cols = ds_logchl.RasterXSize
    rows = ds_logchl.RasterYSize

    # Get the projection information
    proj = ds_logchl.GetProjection()

    # Define the source and target projections
    src_proj = pyproj.Proj(proj)
    target_proj = pyproj.Proj(proj='latlong')

    # Convert the pixel coordinates to geographical coordinates
    x = np.arange(cols) * transform[1] + transform[0]
    y = np.arange(rows) * transform[5] + transform[3]

    xx, yy = np.meshgrid(x, y)

    # Convert the x and y coordinates to longitude and latitude
    latitude = []
    longitude = []

    for ix, iy in zip(xx, yy):
        lon, lat = pyproj.transform(src_proj, target_proj, ix, iy)

        longitude.append(lon)
        latitude.append(lat)

    dict_geo = {'logchl' : ds_logchl.ReadAsArray(),
            'bitmask' : ds_bitmask.ReadAsArray(),
            'longitude' : np.stack(longitude, axis=0),
            'latitude' : np.stack(latitude, axis=0)}

    return dict_geo

def prepare_processor_input(inpath, infile):
    # Prepare the input to OCPFT independently of applied atmospheric correction.
    # Provide masks and geo information and save them.
    # Provide valid Chl-a.

    if ac == 0:

        AC = 'ENPT_ACwater'

        # manin variable for work =  chl-a
        in_varnames = ('logchl')

        geofile = geo(inpath)

        lon = geofile['longitude']
        lat = geofile['latitude']

        qflags = geofile['bitmask']
        l1_flags = qflags[:]

        if isinstance(l1_flags, np.ma.MaskedArray):  # MH: bug fix for py netcdf4 version inconsistency
            l1_flags = np.ma.getdata(l1_flags)

        # MH: valid water pixel according Polymer settings = 0, "Case-2" = 1024, "Inconsistency" = 2048
        # "bitmask" description = LAND:1, CLOUD_BASE:2, L1_INVALID:4, NEGATIVE_BB:8, OUT_OF_BOUNDS:16, EXCEPTION:32, THICK_AEROSOL:64, HIGH_AIR_MASS:128, EXTERNAL_MASK:512, CASE2:1024, INCONSISTENCY:2048

        land = (l1_flags == 1)
        cloud = (l1_flags == 2)
        l1_invalid = (l1_flags == 4)
        negative_BB = (l1_flags == 8)
        out_of_bonds = (l1_flags == 16)
        exception = (l1_flags == 32)
        thick_aerosol = (l1_flags == 64)
        high_air_mass = (l1_flags == 128)
        external_mask = (l1_flags == 512)
        case2 = (l1_flags == 1024)
        inconsistancy = (l1_flags == 2028)
        # land_cloud     = (l1_flags == 3)                                       # MH: not defined mask, but labeled with "3" - likely adjacency pixel

        gerade = (l1_flags % 2 == 0)  # MH: mask all even numbers
        ungerade = np.logical_not(gerade)  # MH: finds everything related to "land"

        water = np.logical_not(land)

        flag_ac_risk = (water & ungerade) | case2

        # MH: in the current version without inland waters (some rivers - not more)!
        invalid_mask = cloud + l1_invalid + negative_BB + out_of_bonds + land + exception + high_air_mass + external_mask + inconsistancy + thick_aerosol

        flag_negative = np.full(land.shape, False, dtype=bool)
        flag_strange = np.full(land.shape, False, dtype=bool)

        b = geofile[in_varnames][:]

        # converting log scale
        b = np.array(10 ** b, dtype=np.float32)

        flag_strange[b > 1] = True  # MH: basically remove any remaining masked data

        valid = np.logical_not(invalid_mask) & np.logical_not(flag_strange)
        flag_negative[b < 0] = True  # MH: marks pixel with any negative Chl_a value

        chl_a = np.ma.array(b, mask = invalid_mask)
        #chl_a = np.ma.masked_array(b, np.logical_not(valid)) # other way to mask

        flag_suspect = (flag_strange & flag_ac_risk)


    if ac == 1:

        AC = 'POLYMER_v_14'

        # manin variable for work =  chl-a
        in_varnames = ('logchl')

        ncfile = nc(os.path.join(inpath, infile), 'r')

        try:
            lon = ncfile.variables['longitude'][:]
            lat = ncfile.variables['latitude'][:]
        except:
            lon = ncfile.variables['lon'][:]
            lat = ncfile.variables['lat'][:]

        qflags = ncfile['bitmask']
        l1_flags = qflags[:]
        print(l1_flags)

        if isinstance(l1_flags, np.ma.MaskedArray):  # MH: bug fix for py netcdf4 version inconsistency
            l1_flags = np.ma.getdata(l1_flags)

        # MH: valid water pixel according Polymer settings = 0, "Case-2" = 1024, "Inconsistency" = 2048
        # "bitmask" description = LAND:1, CLOUD_BASE:2, L1_INVALID:4, NEGATIVE_BB:8, OUT_OF_BOUNDS:16, EXCEPTION:32, THICK_AEROSOL:64, HIGH_AIR_MASS:128, EXTERNAL_MASK:512, CASE2:1024, INCONSISTENCY:2048

        land = (l1_flags == 1)
        cloud = (l1_flags == 2)
        l1_invalid = (l1_flags == 4)
        negative_BB = (l1_flags == 8)
        out_of_bonds = (l1_flags == 16)
        exception = (l1_flags == 32)
        thick_aerosol = (l1_flags == 64)
        high_air_mass = (l1_flags == 128)
        external_mask = (l1_flags == 512)
        case2 = (l1_flags == 1024)
        inconsistancy = (l1_flags == 2028)
        # land_cloud     = (l1_flags == 3)                                       # MH: not defined mask, but labeled with "3" - likely adjacency pixel

        gerade = (l1_flags % 2 == 0)  # MH: mask all even numbers
        ungerade = np.logical_not(gerade)  # MH: finds everything related to "land"

        water = np.logical_not(land)

        flag_ac_risk = (water & ungerade) | case2

        # MH: in the current version without inland waters (some rivers - not more)!
        invalid_mask = cloud + l1_invalid + negative_BB + out_of_bonds + land + exception + high_air_mass + external_mask + inconsistancy + thick_aerosol

        flag_negative = np.full(land.shape, False, dtype=bool)
        flag_strange = np.full(land.shape, False, dtype=bool)

        b = ncfile.variables[in_varnames][:]

        # converting log scale
        b = np.array(10 ** b, dtype=np.float32)

        flag_strange[b > 1] = True  # MH: basically remove any remaining masked data

        valid = np.logical_not(invalid_mask) & np.logical_not(flag_strange)
        flag_negative[b < 0] = True  # MH: marks pixel with any negative Chl_a value

        chl_a = np.ma.array(b, mask = invalid_mask)
        #chl_a = np.ma.masked_array(b, np.logical_not(valid)) # other way to mask

        ncfile.close()

        flag_suspect = (flag_strange & flag_ac_risk)

    # Provides all relevant outputs to other functions
    return chl_a, valid, lat, lon, cloud, land, AC, flag_negative, flag_suspect

def model(data, model):

    ### Define all model functions used in the optimization
    def func_sin(X, a0, a1, a2, a3):  # sigmoidal curve fitting function
        return a0 + a1 * np.sin(a2 * (X + a3))

    def func_exp_3Logistic(X, a0, a1, a2):
        return 1 / (a0 + np.exp(a1 * X + a2))

    def func_exp_5Logistic(X, a0, a1, a2, a3, a4):
        return a0 + (a0 - a1) / (1 + a2 * np.exp(a3 * X + a4))

    if model == 0:
        # array with coefficients for pft
        # sorted by diatoms, cryptophyte, dinoflagellates, prokaryotes, green algae
        coefs = np.array([[0.0207, 0.4203, -0.0077],
                          [-0.0058, 0.2567, 0.1361],
                          [-0.0052, 0.0917, -0.0449],
                          [-0.0024, 0.0818, -0.0252],
                          [-0.0042, 0.0955, -0.0559]])

        X = data.copy()

        # funtion evaluation for each PFT
        PFT = {}

        PFT['chlorophyll_a'] = X

        for i in range(len(coefs)):
            if i == 0:
                vname = 'diatoms'
            if i == 1:
                vname = 'cryptophytes'
            if i == 2:
                vname = 'dinoflagellates'
            if i == 3:
                vname = 'prokaryotes'
            if i == 4:
                vname = 'green_algae'

            poly = np.poly1d(coefs[i])  # generating the function

            PFT[vname] = poly(X)  # applying the model to the Chl-a

        return PFT

    if model == 1:
        # array with coefficients for pft
        # sorted by diatoms, Haptophytes, dinoflagellates, prokaryotes, green algae, prochloroccocus
        coefs =  np.array([[0.4486,	0.3247,	1.1424,	-0.1090],
                          [ 0.1601,	0.1161,	1.8898,	1.2389],
                          [ -0.0116, -0.0082, 0.0246, 0.0611],
                          [ 2.2548,	5.9343,	4.3967,	np.nan],
                          [ 0.1585,	0.0644,	2.5285,	1.1016],
                          [ 5.2002,	8.0185,	6.0039,	np.nan],
                          [ 0.0466, 0.0364, 2.0194, 0.2661]])

        X = np.array(data.copy(), dtype=np.float32)

        # funtion evaluation for each PFT
        PFT = {}

        PFT['chlorophyll_a'] = np.array(10 ** (X))

        for i in range(len(coefs)+1):
            if i == 0:  # sinusoidal
                vname = 'diatoms'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                PFT[vname] = func_sin(X, *coefs_nonan)  # applying the model to the Chl-a

            if i == 1:  # exponential 3 parameters
                vname = 'haptophytes'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                PFT[vname] = func_sin(X, *coefs_nonan) # applying the model to the Chl-a

            if i == 2:  # polynomial order 3
                vname = 'dinoflagellates'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                poly = np.poly1d(coefs_nonan)  # generating the function
                PFT[vname] = poly(X)

            if i == 3: # exponential 3 parameters
                vname = 'prokaryotes'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                PFT[vname] = func_exp_3Logistic(X, *coefs_nonan)  # applying the model to the Chl-a

            if i == 4: # exponential sinusuidal
                vname = 'green_algae'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                PFT[vname] = func_sin(X, *coefs_nonan) # applying the model to the Chl-a

            if i == 5: # exponential 3 parameters
                vname = 'prochloroccocus'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                PFT[vname] = func_exp_3Logistic(X, *coefs_nonan) # applying the model to the Chl-a

            if i == 6:  # exponential 3 parameters
                vname = 'cryptophytes'
                coefs_nonan = coefs[i][~np.isnan(coefs[i])]
                PFT[vname] = func_sin(X, *coefs_nonan)  # applying the model to the Chl-a

        return PFT


def save_results(PFT, outname):

    # One output file for all processor results
    out = nc(outname, 'w')

    # General information on code and data
    out.title = 'OC-PFT Level-2 PFT products based on chlorophyll-a satellite data'
    out.source = 'remote sensing'
    out.sensor = sensor

    out.atmospheric_correction = AC
    out.creation_date = str(dt.now())[:19]

    out.product_name = os.path.basename(outname)

    out.info = 'OC-PFT (Ocean Color Phytoplankton Functional Type) is a water algorithm for retrieve phytoplankton groups chl-a concentration.'
    out.version = version
    out.version_release = release

    out.originator = 'Leonardo Alvarado'
    out.originator_contributer = 'Mariana A. Soppa, Svetlana N. Losa, Astrid Bracher et al.'
    out.originator_institution = 'Alfred Wegener Institute, Helmholtz Centre for Polar and Marine Research, Germany'
    out.contact = 'leonardo.alvarado@awi.de'
    out.project_number = 'DLR-BMWE: 50 EE 1915'

    out.Data_conventions = 'CF-1.6'
    out.crs = 'EPSG:4326'

    ###
    # Save all masks and L1 and L2 information

    out.createDimension('x', valid.shape[0])
    out.createDimension('y', valid.shape[1])

    test = out.createVariable('longitude', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = lon[:, :]

    test.units = 'degrees_east'
    test.standard_name = 'longitude'
    test.long_name = 'Longitude in degrees'
    test.coordinates = 'lat lon'

    test = out.createVariable('latitude', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = lat[:, :]

    test.units = 'degrees_north'
    test.standard_name = 'latitude'
    test.long_name = 'Latitude in degrees'
    test.coordinates = 'lat lon'

    test = out.createVariable('OCPFT_water', 'b', ('x', 'y'), zlib=True)
    test[:, :] = valid[:, :]

    test.units = '1'
    test.standard_name = 'water'
    test.long_name = 'Level_2 mask with non-land and non-cloud pixel that are calculated with POLYMER'
    test.coordinates = 'lat lon'

    test = out.createVariable('land', 'b', ('x', 'y'), zlib=True)
    test[:, :] = land[:, :]

    test.units = '1'
    test.standard_name = 'land'
    test.long_name = 'Level_1 land mask'
    test.coordinates = 'lat lon'

    test = out.createVariable('cloud', 'b', ('x', 'y'), zlib=True)
    test[:, :] = cloud[:, :]

    test.units = '1'
    test.standard_name = 'cloud'
    test.long_name = 'Level_1 cloud mask'
    test.coordinates = 'lat lon'

    test = out.createVariable('chl_a', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = PFT['chlorophyll_a'][:, :]

    test.units = 'molec.cm^{-3}'
    test.standard_name = 'chl_a'
    test.long_name = 'Concentration of Chlorophyll-a'
    test.coordinates = 'lat lon'

    test = out.createVariable('diatom', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = PFT['diatoms'][:, :]

    test.units = 'molec.cm^{-3}'
    test.standard_name = 'diatom'
    test.long_name = 'Concentration of Diatoms'
    test.coordinates = 'lat lon'

    test = out.createVariable('cryp', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = PFT['cryptophytes'][:, :]

    test.units = 'molec.cm^{-3}'
    test.standard_name = 'cryp'
    test.long_name = 'Concentration of Cryptophytes'
    test.coordinates = 'lat lon'

    test = out.createVariable('dino', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = PFT['dinoflagellates'][:, :]

    test.units = 'molec.cm^{-3}'
    test.standard_name = 'dino'
    test.long_name = 'Concentration of Dinoflagellates'
    test.coordinates = 'lat lon'

    test = out.createVariable('proka', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = PFT['prokaryotes'][:, :]

    test.units = 'molec.cm^{-3}'
    test.standard_name = 'proka'
    test.long_name = 'Concentration of Prokaryotes'
    test.coordinates = 'lat lon'

    test = out.createVariable('galg', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
    test[:, :] = PFT['green_algae'][:, :]

    test.units = 'molec.cm^{-3}'
    test.standard_name = 'galg'
    test.long_name = 'Concentration of Green Algae'
    test.coordinates = 'lat lon'

    if model == 1:

        test = out.createVariable('hapt', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
        test[:, :] = PFT['haptophytes'][:, :]

        test.units = 'molec.cm^{-3}'
        test.standard_name = 'hapt'
        test.long_name = 'Concentration of Haptophytes'
        test.coordinates = 'lat lon'

        test = out.createVariable('proch', 'f4', ('x', 'y'), zlib=True, fill_value=np.nan)
        test[:, :] = PFT['prochloroccocus'][:, :]

        test.units = 'molec.cm^{-3}'
        test.standard_name = 'proch'
        test.long_name = 'Concentration of Prochloroccocus sp.'
        test.coordinates = 'lat lon'

    # Close the one output file
    out.close()


### -------------------------------------------------------------------
# MAIN
### -------------------------------------------------------------------

if __name__ == '__main__':
    # print('Usage: ')
    # exit(0)

    start_time = dt.now()

    # Command line parsing # For future applications use CLI
    parser = argparse.ArgumentParser(description='OC-PFT processor')

    parser.add_argument('iprod', action='store', help='Input EnPT-ACwater/Polymer/L2 Chlorophyll-a product')
    parser.add_argument('-od', '--outdir', action='store', help='Output directory, default current directory')
    parser.add_argument('-ofile', '--outfile', action='store', help='Define name of output file')
    parser.add_argument('-sensor', action='store',
                        help='Define used sensor - currently atmospheric corrected data processing of: "EnPT-ACwater" (default; Pol), "OLCI" (Pol), "MSI" (Pol), or "DESIS" (Pol)')
    parser.add_argument('-model', action='store',
                        help='Option for model to use: 0 = lake constance (default), 1 = global (replaced)')
    parser.add_argument('-ac', action='store',
                        help='Define used atmospheric correction: 0 = EnPT-ACwater (default), 1 = POLYMER')
    parser.add_argument('-osize', action='store',
                        help='Define output size: 0 = standard product output (7 products) (default)')

    args = parser.parse_args()

    inpath = os.path.dirname(args.iprod)
    infile = os.path.basename(args.iprod)

    if args.outdir and os.path.isdir(args.outdir):
        outpath = args.outdir
    else:
        outpath = os.getcwd()

        # Output size

        if args.osize == '0':
            output_size = 0  # MH: standard product output (7 products + uncertainty)
        else:
            print(
                'Error: Define "-osize" output size: 0 = standard product output (7 products) (default)')
            sys.exit()

    if args.sensor == 'EnMAP':

        # Sensor specification

        sensor = 'EnMAP'

        if args.model == '0':  # use Lake Constance coefficients

            model = 0
            version = ('_' + version + '_lake_constance')

        elif args.model == '1':  # use global coefficients

            model = 1
            version = ('_' + version + '_global')

        if args.ac == '0':  # EnPT_ACwater
            ac = 0
        elif args.ac == '1':  # POLYMER
            ac = 1

        # Generation of the output file name

        if args.outfile or args.ac == '0':  # MH: if output file name is provided...

            if args.outfile:
                outfile = args.outfile
            else:
                outfile = infile

            if outfile[-3:] == '.nc':
                print('Output file is NETCDF4 file.')
                outname = os.path.join(outpath, outfile)

            elif infile[7] == '1':  # MH: Check if filename includes Level-1 OLCI data

                outfile = list(infile)
                outfile[7] = '2'  # MH: The product will be Level-2

                if args.ac == '0':  # EnPT-ACWater
                    outfile[14] = 'O'
                elif args.ac == '1':  # POLYMER
                    outfile[14] = 'O'

                    print(
                        'Error: Provide atmospheric corrected (Level-2) (EnPT-ACWater, or POL). ')
                    sys.exit()

                    # ac              = 3
                    # outfile[14]     = 'O'

                outfile = ''.join(outfile)

                outname = os.path.join(outpath, outfile[:-3] + '_' + str(output_size) + str(version) + '.nc')


                outfile = ''.join(outfile)

                outname = os.path.join(outpath, outfile[:-3] + '_' + str(output_size) + str(version) + '.nc')

    if args.sensor == 'OLCI':

        # Sensor specification

        sensor = 'OLCI'

        if args.model == '0':  # use Lake Constance coefficients

            model = 0
            version = ('_' + version + '_lake_constance')

        elif args.model == '1':  # use global coefficients

            model = 1
            version = ('_' + version + '_global')

        if args.ac == '0':  # EnPT_ACwater
            ac = 0
        elif args.ac == '1':  # POLYMER
            ac = 1

        # Generation of the output file name

        if args.outfile or args.ac == '0':  # MH: if output file name is provided...

            if args.outfile:
                outfile = args.outfile
            else:
                outfile = infile

            if outfile[-3:] == '.nc':
                print('Output file is NETCDF4 file.')
                outname = os.path.join(outpath, outfile)

            elif infile[7] == '1':  # MH: Check if filename includes Level-1 OLCI data

                outfile = list(infile)
                outfile[7] = '2'  # MH: The product will be Level-2

                if args.ac == '0':  # EnPT-ACWater
                    outfile[14] = 'O'
                elif args.ac == '1':  # POLYMER
                    outfile[14] = 'O'

                    print(
                        'Error: Provide atmospheric corrected (Level-2) (EnPT-ACWater, or POL). ')
                    sys.exit()

                    # ac              = 3
                    # outfile[14]     = 'O'

                outfile = ''.join(outfile)

                outname = os.path.join(outpath, outfile[:-3] + '_' + str(output_size) + str(version) + '.nc')


                outfile = ''.join(outfile)

                outname = os.path.join(outpath, outfile[:-3] + '_' + str(output_size) + str(version) + '.nc')


            else:

                outfile = infile

                outname = os.path.join(outpath, outfile)

                print('Warning: Input file name is not according to OLCI convention.')

    ######################## TEST PLOTTING ######################
# import matplotlib
# matplotlib.use("TkAgg")
# import matplotlib.pyplot as plt
# import matplotlib as mpl
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
#
# import matplotlib.dates as mdates
#
# from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
# from mpl_toolkits.axes_grid1 import make_axes_locatable
#
# ac = 1
# chl_a, valid, lat, lon, cloud, land, AC, flag_negative, flag_suspect = prepare_processor_input(inpath,infile)
#
#
# fig, ax = plt.subplots(1, 1, subplot_kw=dict(projection=ccrs.PlateCarree()))
#
# # region to plot
# ax.set_extent((9.0, 9.6, 47.45, 47.85))
# arr = chl_a
# #arr = arr[valid]
#
# #arr = arr[~arr.mask]
#
# #lat, lon = ds.variables['latitude'][:], ds.variables['longitude'][:]
#
# cmap = plt.get_cmap('viridis')
#
# im = ax.pcolormesh(lon, lat, arr, shading="auto", vmin=0, vmax=5,
#                    cmap=cmap, transform=ccrs.PlateCarree())
#
# ax.add_feature(cfeature.COASTLINE)
# ax.add_feature(cfeature.LAND, facecolor='0.95')
#
# lon_formatter = LongitudeFormatter()
# lat_formatter = LatitudeFormatter()
# ax.set_yticks(np.linspace(47.45 + 0.05, 47.85 - 0.05, 5),
#               crs=ccrs.PlateCarree())
# ax.set_xticks(np.linspace(9.0, 9.6, 7),
#               crs=ccrs.PlateCarree())
# ax.xaxis.set_major_formatter(lon_formatter)
# ax.yaxis.set_major_formatter(lat_formatter)
#
# ax.gridlines()
#
# # changing the size of ticks
# ax.tick_params(width=1, length=5)
#
# fig.colorbar(im, label='Chl-a', orientation='horizontal',
#              extend='both',
#              )
#######################################################################
