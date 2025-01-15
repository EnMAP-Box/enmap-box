import os
import geopandas as gpd
from shapely.geometry import Polygon
from osgeo import gdal
import pandas as pd
import math

def split_raster_rois(source_raster, source_mask, roi_s, output_path, tile_size_x, tile_size_y, x_stride, y_stride,
                      mode=True, remove_null=True):
    # Create directories
    # os.mkdir(output_path)#
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    image_dir = os.path.join(output_path, 'images')
    label_dir = os.path.join(output_path, 'labels')
    os.mkdir(image_dir)
    os.mkdir(label_dir)

    # open rasters
    ds = gdal.Open(source_raster)
    ds_mask = gdal.Open(source_mask)


    # assert checks if same crs or pixel sizes in x and y
    prj_ds =ds.GetProjection()
    prj_ds_mask = ds_mask.GetProjection()
    assert prj_ds == prj_ds_mask, "The rasters have different CRS."
    assert ds.GetGeoTransform()[1] == ds_mask.GetGeoTransform()[
        1], "The rasters have different pixel sizes in X direction."
    assert ds.GetGeoTransform()[5] == ds_mask.GetGeoTransform()[
        5], "The rasters have different pixel sizes in X direction."
    # add assert to check same extent and also if roi is on raster?

    # get  raster image name
    r_name = os.path.basename(source_raster)
    r_name = r_name[:-4]

    # mask rasters oustide rois
    masked_ds = gdal.Warp('d', ds, format='MEM', cutlineDSName=roi_s, cropToCutline=False, dstNodata=0)
    masked_ds_mask = gdal.Warp('m', ds, format='MEM', cutlineDSName=roi_s, cropToCutline=False, dstNodata=0)

    # transform stride and tile pixel size to geo. unit

    pixel_size_x = ds.GetGeoTransform()[1]
    pixel_size_y = abs(ds.GetGeoTransform()[5])

    xOrigin = ds.GetGeoTransform()[0]
    yOrigin = ds.GetGeoTransform()[3]

    x_stride_geo = pixel_size_x * x_stride
    y_stride_geo = pixel_size_y * y_stride
    x_tile_size_geo = tile_size_x * pixel_size_x
    y_tile_size_geo = tile_size_y * pixel_size_y

    # Read rois
    gdf = gpd.read_file(roi_s)

    # create extra column with polygon coordinates boundaries
    gdf = pd.concat([gdf, gdf.bounds], axis=1)

    for index, row in gdf.iterrows():

        # get polygon bounding box per roi
        x_min, y_min, x_max, y_max, polygon = row['minx'], row['miny'], row['maxx'], row['maxy'], row['geometry']

        #### next lines adapted from https://github.com/deepbands/deep-learning-datasets-maker/blob/develop/deep-learning-datasets-maker/utils/splitting.py

        x_tile_num = math.ceil((x_max - x_min) / x_tile_size_geo)
        y_tile_num = math.ceil((y_max - abs(y_min)) / y_tile_size_geo)  # very strong adapted ()

        # create lists of x and y coordinates range function needs integer:
        xsteps = [x_min + x_stride_geo * i for i in range(
            x_tile_num)]  # stride instead tile size adapted , + 1 removed as goes over bounds anyway, through tile size
        ysteps = [y_max - y_stride_geo * i for i in range(y_tile_num)]

        # total steps is xsteps * y_steps for progress bar n
        # or add time sleep at for loop for j* then progress is not shown by tile but by row , also okay

        # loop over min and max x and y coordinates
        for i in range(x_tile_num):  # change list name
            for j in range(y_tile_num):
                xmin = xsteps[i]
                xmax = xsteps[
                           i] + x_tile_size_geo  # adapted here + tile size instead of next value ( important as stride is used for steps)
                ymax = ysteps[j]
                ymin = ysteps[j] - y_tile_size_geo
                ##### adapted until here

                projwin = (
                    xmin, ymax, xmax, ymin)  ##### does this need abs to work? , other raster tile geneartor does it

                # create polygon for each tile
                sub_window_polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])

                # check if tile is contained in rois, if mode is 2
                if mode == False:

                    if polygon.contains(sub_window_polygon) == True:

                        if remove_null == True:
                            xOffset = int((xmin - xOrigin) / pixel_size_x)
                            yOffset = int(abs((ymax - yOrigin) / pixel_size_y))
                            window_array = ds_mask.ReadAsArray(xOffset, yOffset, tile_size_x, tile_size_y)
                            if (window_array != 0).any():
                                output = f'{r_name}_roi{index}_{i}_{j}.tif'
                                path_i_out = os.path.join(image_dir, output)
                                path_l_out = os.path.join(label_dir, output)
                                # replace proj win
                                gdal.Translate(path_i_out, ds, srcWin=[xOffset, yOffset, tile_size_x, tile_size_y])
                                gdal.Translate(path_l_out, ds_mask, srcWin=[xOffset, yOffset, tile_size_x, tile_size_y])
                                print(f"Tile  {output} is created as within  ROI")
                            else:
                                # gdal.Translate(path_l_out , ds_mask, srcWin=[x, y, tile_size_x, tile_size_y])
                                output = f'{r_name}_roi{index}_{i}_{j}.tif'
                                print(f"Tile  {output} is not created as no valid class pixels")
                                # continue : continue statement not needed?
                        else:
                            output = f'{r_name}_roi{index}_{i}_{j}.tif'
                            path_i_out = os.path.join(image_dir, output)
                            path_l_out = os.path.join(label_dir, output)
                            # replace proj win
                            gdal.Translate(path_i_out, ds, projWin=projwin)
                            gdal.Translate(path_l_out, ds_mask, projWin=projwin)
                            print(f"Tile  {output} is created as within  ROI")

                        # check if tile is contained or intersect with rois, if mode is 3
                elif mode == True:
                    if polygon.contains(sub_window_polygon) == True or polygon.intersects(sub_window_polygon) == True:
                        if remove_null == True:
                            xOffset = int((xmin - xOrigin) / pixel_size_x)
                            yOffset = int(abs((ymax - yOrigin) / pixel_size_y))
                            window_array = ds_mask.ReadAsArray(xOffset, yOffset, tile_size_x, tile_size_y)
                            if (window_array != 0).any():
                                output = f'{r_name}_roi{index}_{i}_{j}.tif'
                                path_i_out = os.path.join(image_dir, output)
                                path_l_out = os.path.join(label_dir, output)
                                # replace proj win
                                gdal.Translate(path_i_out, masked_ds,
                                               srcWin=[xOffset, yOffset, tile_size_x, tile_size_y])
                                gdal.Translate(path_l_out, masked_ds_mask,
                                               srcWin=[xOffset, yOffset, tile_size_x, tile_size_y])
                                print(f"Tile  {output} is created as within or intersecting with ROI")
                            else:
                                # gdal.Translate(path_l_out , ds_mask, srcWin=[x, y, tile_size_x, tile_size_y])
                                output = f'{r_name}_roi{index}_{i}_{j}.tif'
                                print(f"Tile  {output} is not created as no valid class pixels")
                                # continue : continue statement not needed?
                        else:
                            output = f'{r_name}_roi{index}_{i}_{j}.tif'
                            path_i_out = os.path.join(image_dir, output)
                            path_l_out = os.path.join(label_dir, output)
                            # replace proj win
                            gdal.Translate(path_i_out, masked_ds, projWin=projwin)
                            gdal.Translate(path_l_out, masked_ds_mask, projWin=projwin)
                            print(f"Tile  {output} is created as within or intersecting with ROI")
                            # else:
                # gdal.Translate(path_l_out , ds_mask, srcWin=[x, y, tile_size_x, tile_size_y])
                # output = f'output_tile_roi{index}_{i}_{j}.tif'
                # print(f"Tile  {output} is not created as no valid class pixels")
                # continue : continue statement not needed?
    ds = None
    ds_mask = None
    masked_ds = None
    masked_ds_mask = None
