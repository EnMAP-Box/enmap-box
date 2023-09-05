import os
import platform
import warnings
from os.path import join, dirname, abspath
from typing import Optional

import enmapbox.exampledata

_root = abspath(join(dirname(dirname(__file__)), 'testdata'))

# Berlin example data
# ...this is the old example dataset, which we still need for unittests
_subdir = 'exampledata/berlin'
enmap_berlin = join(_root, _subdir, 'enmap_berlin.bsq')
enmap_srf_library = join(dirname(__file__), 'enmap_srf_library.gpkg')
hires_berlin = join(_root, _subdir, 'hires_berlin.bsq')
landcover_berlin_point = join(_root, _subdir, 'landcover_berlin_point.gpkg')
landcover_berlin_polygon = join(_root, _subdir, 'landcover_berlin_polygon.gpkg')
library_berlin = join(_root, _subdir, 'library_berlin.gpkg')
veg_cover_fraction_berlin_point = join(_root, _subdir, 'veg-cover-fraction_berlin_point.gpkg')

# Potsdam example data
# ...current example dataset is placed under enmapbox.exampledata
aerial_potsdam = enmapbox.exampledata.aerial
enmap_potsdam = enmapbox.exampledata.enmap
landcover_potsdam_polygon = enmapbox.exampledata.landcover_potsdam_polygon
landcover_potsdam_point = enmapbox.exampledata.landcover_potsdam_point

# connect old shortcuts (requested by @jakimow)
enmap = enmap_berlin
hires = hires_berlin
library_gpkg = library_berlin

# RASTER
_subdir = 'raster'
# - rasterized landcover polygons
landcover_polygon_1m = join(_root, _subdir, 'landcover_polygon_1m.tif')
landcover_polygon_1m_3classes = join(_root, _subdir, 'landcover_polygon_1m_3classes.tif')
landcover_polygon_1m_epsg3035 = join(_root, _subdir, 'landcover_polygon_1m_EPSG3035.tif')
landcover_polygon_30m = join(_root, _subdir, 'landcover_polygon_30m.tif')
landcover_polygon_30m_epsg3035 = join(_root, _subdir, 'landcover_polygon_30m_EPSG3035.tif')

# - landcover maps (predicted by RF)
landcover_map_l2 = join(_root, _subdir, 'landcover_map_l2.tif')
landcover_map_l3 = join(_root, _subdir, 'landcover_map_l3.tif')

# - rasterized landcover polygon fractions
fraction_polygon_l3 = join(_root, _subdir, 'fraction_polygon_l3.tif')

# - landcover fraction maps (predicted by RF)
fraction_map_l3 = join(_root, _subdir, 'fraction_map_l3.tif')

# - binary water mask (derived from landcover map)
water_mask_30m = join(_root, _subdir, 'water_mask_30m.tif')

# - 300m grid (same extent as 30m rasters)
enmap_grid_300m = join(_root, _subdir, 'enmap_grid_300m.vrt')

# VECTOR
_subdir = 'vector'

# - landcover polygons
landcover_polygon = landcover_berlin_polygon
landcover_polygon_3classes = join(_root, _subdir, 'landcover_polygon_3classes.gpkg')
landcover_polygon_3classes_id = join(_root, _subdir, 'landcover_polygon_3classes_id.gpkg')
landcover_polygon_3classes_epsg4326 = join(_root, _subdir, 'landcover_polygon_3classes_EPSG4326.gpkg')

# - landcover points
landcover_point = landcover_berlin_point
landcover_points_singlepart_epsg3035 = join(_root, _subdir, 'landcover_point_singlepart_3035.gpkg')
landcover_points_multipart_epsg3035 = join(_root, _subdir, 'landcover_point_multipart_3035.gpkg')

# - landcover fraction points
fraction_point_multitarget = join(_root, _subdir, 'fraction_point_multitarget.gpkg')
fraction_point_singletarget = join(_root, _subdir, 'fraction_point_singletarget.gpkg')

points_in_no_data_region = join(_root, _subdir, 'points_in_no_data_region.gpkg')

# LIBRARY
_subdir = 'library'
library = join(_root, _subdir, 'library.gpkg')
landsat8_srf = join(_root, _subdir, 'landsat8_srf.gpkg')

# DATASET
_subdir = 'ml'

# - Classifier
classifierDumpPkl = join(_root, _subdir, 'classifier.pkl')

# - Classification dataset
classificationDatasetAsGpkgVector = join(_root, _subdir, 'classification_dataset.gpkg')
classificationDatasetAsCsvVector = join(_root, _subdir, 'classification_dataset.csv')
classificationDatasetAsJsonFile = join(_root, _subdir, 'classification_dataset.json')
classificationDatasetAsPklFile = join(_root, _subdir, 'classification_dataset.pkl')
classificationDatasetAsForceFile = (
    join(_root, _subdir, 'classification_dataset_force_features.csv'),
    join(_root, _subdir, 'classification_dataset_force_labels.csv')
)

# - Regressor
regressorDumpPkl = join(_root, _subdir, 'regressor.pkl')
regressorDumpSingleTargetPkl = join(_root, _subdir, 'regressor_singletarget.pkl')
regressorDumpMultiTargetPkl = join(_root, _subdir, 'regressor_multitarget.pkl')

# - Regression dataset
regressionDatasetAsJsonFile = join(_root, _subdir, 'regression_dataset.json')
regressionDatasetAsPkl = join(_root, _subdir, 'regression_dataset.pkl')

# external testdata
_subdir = 'external'
engeomap_cubus_gamsberg_subset = join(_root, _subdir, 'engeomap', 'cubus_gamsberg_subset')
engeomap_gamsberg_field_library = join(_root, _subdir, 'engeomap', 'gamsberg_field_library')
engeomap_gamesberg_field_library_color_mod = join(_root, _subdir, 'engeomap', 'gamesberg_field_library_color_mod.csv')
del _subdir, _root


# external sensor products
def sensorProductsRoot() -> Optional[str]:
    # - let's have some developer-dependent default locations
    root = None
    try:
        root = {
            'Andreas@PC-21-0602': r'd:\data\sensors'
        }.get(os.getlogin() + '@' + platform.node())
    except OSError as ex:
        warnings.warn(f'Exception raised in sensorProductsRoot():\n{ex}')

    # - check environment variable
    if root is None:
        root = os.environ.get('ENMAPBOX_SENSOR_PRODUCT_ROOT')

    return root


class SensorProducts(object):
    if sensorProductsRoot() is not None:
        class Desis(object):
            L1B = join(
                sensorProductsRoot(), 'desis', 'DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210'
            )
            L1B_MetadataXml = join(
                L1B, 'DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210-METADATA.xml'
            )
            L1C = join(
                sensorProductsRoot(), 'desis', 'DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210'
            )
            L1C_MetadataXml = join(
                L1C, 'DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210-METADATA.xml'
            )
            L2A = join(
                sensorProductsRoot(), 'desis', 'DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210'
            )
            L2A_MetadataXml = join(
                L2A, 'DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210-METADATA.xml'
            )

        class Emit(object):
            L2A = join(sensorProductsRoot(), 'EMIT', 'EMIT_L2A')
            L2A_RFL = join(L2A, 'EMIT_L2A_RFL_001_20230204T101746_2303507_043.nc')

        class Enmap(object):
            L1B = join(
                sensorProductsRoot(), 'enmap',
                'ENMAP01-____L1B-DT0000004135_20221005T023547Z_010_V010106_20221014T102746Z'
            )
            L1B_MetadataXml = join(
                L1B, 'ENMAP01-____L1B-DT0000004135_20221005T023547Z_010_V010106_20221014T102746Z-METADATA.XML'
            )
            L1C = join(
                sensorProductsRoot(), 'enmap',
                'ENMAP01-____L1C-DT0000004135_20221005T023547Z_010_V010106_20221014T102747Z'
            )
            L1C_MetadataXml = join(
                L1C, 'ENMAP01-____L1C-DT0000004135_20221005T023547Z_010_V010106_20221014T102747Z-METADATA.XML'
            )
            L2A = join(
                sensorProductsRoot(), 'enmap',
                'ENMAP01-____L2A-DT0000004135_20221005T023547Z_010_V010106_20221014T102749Z'
            )
            L2A_MetadataXml = join(
                L2A, 'ENMAP01-____L2A-DT0000004135_20221005T023547Z_010_V010106_20221014T102749Z-METADATA.XML'
            )

        class Landsat(object):  # collection 2 only

            LC09_L1 = join(sensorProductsRoot(), 'landsat', 'LC09_L1TP_193023_20220320_20220322_02_T1')
            LC09_L1_MtlTxt = join(LC09_L1, 'LC09_L1TP_193023_20220320_20220322_02_T1_MTL.txt')

            LC09_L2 = join(sensorProductsRoot(), 'landsat', 'LC09_L2SP_001053_20220215_20220217_02_T1')
            LC09_L2_MtlTxt = join(LC09_L2, 'LC09_L2SP_001053_20220215_20220217_02_T1_MTL.txt')

            LC08_L1 = join(sensorProductsRoot(), 'landsat', 'LC08_L1TP_193023_20220312_20220321_02_T1')
            LC08_L1_MtlTxt = join(LC08_L1, 'LC08_L1TP_193023_20220312_20220321_02_T1_MTL.txt')

            LC08_L2 = join(sensorProductsRoot(), 'landsat', 'LC08_L2SP_192023_20210724_20210730_02_T1')
            LC08_L2_MtlTxt = join(LC08_L2, 'LC08_L2SP_192023_20210724_20210730_02_T1_MTL.txt')

            LE07_L1 = join(sensorProductsRoot(), 'landsat', 'LE07_L1TP_193023_20220320_20220415_02_T1')
            LE07_L1_MtlTxt = join(LE07_L1, 'LE07_L1TP_193023_20220320_20220415_02_T1_MTL.txt')

            LE07_L2 = join(sensorProductsRoot(), 'landsat', 'LE07_L2SP_193023_20210605_20210701_02_T1')
            LE07_L2_MtlTxt = join(LE07_L2, 'LE07_L2SP_193023_20210605_20210701_02_T1_MTL.txt')

            LT05_L1 = join(sensorProductsRoot(), 'landsat', 'LT05_L1TP_193023_20110602_20200822_02_T1')
            LT05_L1_MtlTxt = join(LT05_L1, 'LT05_L1TP_193023_20110602_20200822_02_T1_MTL.txt')

            LT05_L2 = join(sensorProductsRoot(), 'landsat', 'LT05_L2SP_192024_20111102_20200820_02_T1')
            LT05_L2_MtlTxt = join(LT05_L2, 'LT05_L2SP_192024_20111102_20200820_02_T1_MTL.txt')

            LT04_L1 = join(sensorProductsRoot(), 'landsat', 'LT04_L1TP_192023_19881110_20200917_02_T1')
            LT04_L1_MtlTxt = join(LT04_L1, 'LT04_L1TP_192023_19881110_20200917_02_T1_MTL.txt')

            LT04_L2 = join(sensorProductsRoot(), 'landsat', 'LT04_L2SP_193025_19880610_20200917_02_T1')
            LT04_L2_MtlTxt = join(LT04_L2, 'LT04_L2SP_193025_19880610_20200917_02_T1_MTL.txt')

            LM05_L1 = join(sensorProductsRoot(), 'landsat', 'LM05_L1TP_192023_20120917_20200820_02_T2')
            LM05_L1_MtlTxt = join(LM05_L1, 'LM05_L1TP_192023_20120917_20200820_02_T2_MTL.txt')

            LM04_L1 = join(sensorProductsRoot(), 'landsat', 'LM04_L1TP_193023_19830901_20210907_02_T2')
            LM04_L1_MtlTxt = join(LM04_L1, 'LM04_L1TP_193023_19830901_20210907_02_T2_MTL.txt')

            LM03_L1 = join(sensorProductsRoot(), 'landsat', 'LM03_L1TP_209023_19820729_20210927_02_T2')
            LM03_L1_MtlTxt = join(LM03_L1, 'LM03_L1TP_209023_19820729_20210927_02_T2_MTL.txt')

            LM02_L1 = join(sensorProductsRoot(), 'landsat', 'LM02_L1TP_208023_19761205_20200907_02_T2')
            LM02_L1_MtlTxt = join(LM02_L1, 'LM02_L1TP_208023_19761205_20200907_02_T2_MTL.txt')

            LM01_L1 = join(sensorProductsRoot(), 'landsat', 'LM01_L1TP_207023_19750429_20200908_02_T2')
            LM01_L1_MtlTxt = join(LM01_L1, 'LM01_L1TP_207023_19750429_20200908_02_T2_MTL.txt')

        class Prisma(object):
            L1 = join(sensorProductsRoot(), 'prisma', 'PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5')
            L2B = join(sensorProductsRoot(), 'prisma', 'PRS_L2B_STD_20201107101404_20201107101408_0001.he5')
            L2C = join(sensorProductsRoot(), 'prisma', 'PRS_L2C_STD_20201107101404_20201107101408_0001.he5')
            L2D = join(sensorProductsRoot(), 'prisma', 'PRS_L2D_STD_20201107101404_20201107101408_0001.he5')

        class Sentinel2(object):
            S2A_L1C = join(
                sensorProductsRoot(), 'sentinel2', 'S2A_MSIL1C_20220720T101611_N0400_R065_T33UUU_20220720T140828.SAFE'
            )
            S2A_L1C_MsiL1CXml = join(S2A_L1C, 'MTD_MSIL1C.xml')

            S2A_L2A = join(
                sensorProductsRoot(), 'sentinel2', 'S2A_MSIL2A_20200816T101031_N0214_R022_T32UQD_20200816T130108.SAFE'
            )
            S2A_L2A_MsiL1CXml = join(S2A_L2A, 'MTD_MSIL2A.xml')

            S2B_L1C = join(
                sensorProductsRoot(), 'sentinel2', 'S2B_MSIL1C_20211028T102039_N0301_R065_T33UUU_20211028T110445.SAFE'
            )
            S2B_L1C_MsiL1CXml = join(S2B_L1C, 'MTD_MSIL1C.xml')

            S2B_L2A = join(
                sensorProductsRoot(), 'sentinel2', 'S2B_MSIL2A_20211028T102039_N0301_R065_T33UUU_20211028T121942.SAFE'
            )
            S2B_L2A_MsiL1CXml = join(S2B_L2A, 'MTD_MSIL2A.xml')
