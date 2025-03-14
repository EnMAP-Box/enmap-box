
import os
import geopandas as gpd
from osgeo import gdal
from osgeo.gdal_array import DatasetWriteArray
import pandas as pd
import math
import numpy as np
from qgis._core import QgsProcessingFeedback


def split_raster(raster, ds_mask, output_path, tile_size_x, tile_size_y, step_x, step_y,
                 remove_null_int=10, feedback:QgsProcessingFeedback=None):  # no_data_value= 0 removed and fixed to 0
    # add assert raster size ds and mask same, and crs, and pixel size,
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    image_dir = os.path.join(output_path, 'images')
    label_dir = os.path.join(output_path, 'labels')
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    if not os.path.exists(label_dir):
        os.makedirs(label_dir)


    # get  raster image name
    r_name = os.path.basename(raster)
    r_name = r_name[:-4]

    ## read raster
    ds = gdal.Open(raster)
    ds_mask = gdal.Open(ds_mask)

    #  get Mask meta data
    data_type = ds_mask.GetRasterBand(1).DataType
    projection = ds_mask.GetProjection()

    if remove_null_int > 0:
        #######
        # create no data mask from spectral image first channel before continuing
        spec_band = ds.GetRasterBand(1)
        nodata_spec = spec_band.GetNoDataValue()
        # Read data from modified raster
        if nodata_spec is not None:

            data_arr = spec_band.ReadAsArray()
            # data_arr = dataset.ReadAsArray(0)

            mask = (data_arr == nodata_spec)

            # mask label raster with no data mask
            band = ds_mask.ReadAsArray()

            # reserved no data label class 0
            band[mask] = 0 # or use no_data_value from interface to over-burn   ### changed. fixed to 0 for no data label
        else:
            band = ds_mask.ReadAsArray()

        #######
        ####### Do this pad before loop
        ####### this padding is only at the end sides of image and add tile length and width. as only endside, doesnt influence xy indexing in for loop)
        ####### (gdal tranlsate write over image bounds, only for np. read important)
        #######

        extended_array = np.pad(band, ((0, tile_size_y), (0, tile_size_x)), mode='constant', constant_values=0)
        original_width = ds.RasterXSize
        original_height = ds.RasterYSize
        original_band = ds.GetRasterBand(1)  # Assuming single-band raster

        # Calculate the dimensions of the new raster
        new_width = original_width + tile_size_x
        new_height = original_height + tile_size_y

        # Create an in-memory raster with the new dimensions
        driver = gdal.GetDriverByName('MEM')
        new_dataset = driver.Create('', new_width, new_height, 1, original_band.DataType)

        # Set the geotransform and projection from the original raster
        new_dataset.SetGeoTransform(ds.GetGeoTransform())
        new_dataset.SetProjection(ds.GetProjection())

        # Read the data from the original raster and write it to the new raster
        # data = original_band.ReadAsArray(0, 0, original_width, original_height)
        new_dataset.GetRasterBand(1).WriteArray(extended_array, 0, 0)
        ds_mask = new_dataset

    total_tiles = ((ds.RasterXSize // step_x) + 1) * ((ds.RasterYSize // step_y) + 1)
    counter = 0
    tile_counter =0


    for x in range(0, ds.RasterXSize, step_x):  # inklusiv +1
        for y in range(0, ds.RasterYSize,
                       step_y):  ### change order here, so in line with direction of tile production of polygon tiler generater

            ##if remove_null == True:

            ####if  remove_null_percent >

            if remove_null_int > 0:
                mask_array = ds_mask.ReadAsArray(x, y, tile_size_x, tile_size_y)
                #image_array = ds.ReadAsArray(x, y, tile_size_x, tile_size_y)
                # Create a mask for all bands where the mask is zero
                #mask = (mask_array != 0)

                # Apply the mask to all bands of the image
                #masked_image_array = image_array * mask

                # changed fixed to 0 as no_data_label
                non_zero_percentage = np.sum(mask_array != 0) / mask_array.size
                # Check if more than 50% of the values are not zero

                remove_null_percent = remove_null_int/100
                if non_zero_percentage >= remove_null_percent:
                    output = f'{r_name}_tile_{x}_{y}.tif'
                    path_i_out = os.path.join(image_dir, output)
                    path_l_out = os.path.join(label_dir, output)
                    gdal.Translate(path_i_out, ds, srcWin=[x, y, tile_size_x, tile_size_y])
                    gdal.Translate(path_l_out, ds_mask, srcWin=[x, y, tile_size_x, tile_size_y])
                    print(f"Created {output}")
                    tile_counter +=1
                else:
                    output = f'{r_name}_tile_{x}_{y}.tif'
                    print(f"Not created {output}")

            else:
                output = f'{r_name}_tile_{x}_{y}.tif'
                path_i_out = os.path.join(image_dir, output)
                path_l_out = os.path.join(label_dir, output)
                gdal.Translate(path_i_out, ds, srcWin=[x, y, tile_size_x, tile_size_y])
                gdal.Translate(path_l_out, ds_mask, srcWin=[x, y, tile_size_x, tile_size_y])
                print(f"Created {output}")
                tile_counter += 1

            counter += 1

            progress = (counter / total_tiles) * 100
            if isinstance(feedback, QgsProcessingFeedback):
                feedback.setProgress(progress)

                # Allow user to cancel the process
                if feedback.isCanceled():
                    break


    new_dataset = None
    ds = None
    ds_mask = None

    return  tile_counter

