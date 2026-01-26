# from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any

import numpy as np
from osgeo import ogr, gdal

from _classic.hubdc.core import RasterDataset, VectorDataset, Point, Pixel, Geometry, Extent, MemDriver, GeoPackageDriver


def sample_points(raster: RasterDataset, vector: VectorDataset, idField=None) -> Dict[str, List[Pixel]]:
    samples = defaultdict(list)
    vector.setSpatialFilter(raster.grid().extent().geometry())
    for feature in vector.features():
        if idField is None:
            id = feature.ogrFeature().GetFID()
        else:
            id = feature.value(attribute=idField)
        typename = vector.geometryTypeName().upper().replace(' ', '')
        if typename == 'MULTIPOINT':
            wkt: str = feature.geometry().ogrGeometry().ExportToWkt()
            for s in wkt[wkt.find('(') + 1: -1].split(','):
                x, y = map(float, s.split(' '))
                point = Point(x=x, y=y, projection=vector.projection())
                pixel = raster.grid().pixelCoordinate(point=point)
                samples[id].append(pixel)
        else:
            assert 0
    vector.unsetSpatialFilter()
    return samples


def sample_polygons_iterateOverFeatures(
        raster: RasterDataset, vector: VectorDataset, idField: str = None, oversampling=1, allTouched=False
) -> Dict[str, List[Tuple[float, Pixel]]]:
    samples = defaultdict(list)
    vector.setSpatialFilter(raster.grid().extent().geometry())
    typename = None
    driver = MemDriver()
    for i1, feature in enumerate(vector.features()):
        print(i1, '/', vector.featureCount())
        if idField is None:
            id = feature.ogrFeature().GetFID()
        else:
            id = feature.value(attribute=idField)
        if typename is None:
            typename = feature.geometry().typeName().upper().replace(' ', '')
        if typename == 'MULTIPOLYGON':
            ogrGeometry: ogr.Geometry
            geometryWkts = [g.ExportToWkt() for g in feature.geometry().ogrGeometry()]
            for i2, geometryWkt in enumerate(geometryWkts):
                print(i2, '/', len(geometryWkts))
                geometry = Geometry(wkt=geometryWkt, projection=vector.projection())
                memvector = VectorDataset.fromPolygons(
                    geometries=[geometry])  # , filename=f'data/vector_{id}_{i1}_{i2}.gpkg', driver=GeoPackageDriver())

                extent = Extent.fromGeometry(geometry=geometry)
                buffer = max(raster.grid().resolution().x(), raster.grid().resolution().y())
                extentBuffered = extent.buffer(buffer=buffer)
                grid = raster.grid().clip(extent=extentBuffered)
                gridOversampled = grid.atResolution(resolution=grid.resolution() / oversampling)
                memraster = memvector.rasterize(
                    grid=gridOversampled, gdalType=gdal.GDT_Float32, allTouched=allTouched, driver=driver
                ).translate(grid=grid, resampleAlg=gdal.GRA_Average)
                # memraster.translate(filename=f'data/raster_{id}_{i1}_{i2}.bsq')
                array = memraster.readAsArray()[0]
                valid = array > 0
                offset = raster.grid().pixelCoordinate(point=grid.extent().upperLeft())
                xarray = memraster.grid().xPixelCoordinatesArray(offset=offset.x())
                yarray = memraster.grid().yPixelCoordinatesArray(offset=offset.y())

                for w, x, y in zip(array[valid], xarray[valid], yarray[valid]):
                    samples[id].append((w, Pixel(x=x, y=y)))
            print(samples[id])
        else:
            assert 0, typename
        break
    vector.unsetSpatialFilter()
    return samples


def sample_polygons(
        raster: RasterDataset, vector: VectorDataset, fieldNames: List[str] = None,
        oversampling=1, allTouched=False
) -> List['Sample']:
    if fieldNames is None:
        fieldNames = []

    assert set(fieldNames).issubset(vector.fieldNames())

    vector.setSpatialFilter(raster.grid().extent().geometry())
    driver = MemDriver()

    grid = raster.grid()
    gridOversampled = grid.atResolution(resolution=grid.resolution() / oversampling)

    xarray = grid.xPixelCoordinatesArray()
    yarray = grid.yPixelCoordinatesArray()

    fidName = '_fid'
    memvector = vector.createFidDataset(filename='/vsimem/sample_polygons/fid.gpkg')

    fidRaster = memvector.rasterize(
        grid=gridOversampled, gdalType=gdal.GDT_Float32, initValue=-1, allTouched=allTouched, driver=driver,
        burnAttribute=fidName
    )  # .translate(grid=grid, resampleAlg=gdal.GRA_Average)
    fidRaster.translate(filename=f'data/raster_fid.bsq')
    fidArray = fidRaster.readAsArray()

    samples = list()
    # aggregate back to target resolution
    dataArray = raster.readAsArray()

    for feature, memfeature in zip(vector.features(), memvector.features()):
        fid = memfeature.value(fidName)
        fieldValues = [feature.value(fieldName) for fieldName in fieldNames]
        maskArray = (fidArray == fid).astype(np.float32)
        maskRaster = RasterDataset.fromArray(
            array=maskArray, grid=gridOversampled
        ).translate(
            grid=grid, resampleAlg=gdal.GRA_Average
        )
        weightArray = maskRaster.readAsArray()[0]
        valid = weightArray > 0
        weights = weightArray[valid]
        xLocations = xarray[valid]
        yLocations = yarray[valid]
        profiles = dataArray[:, yLocations, xLocations].T
        sample = Sample(
            fid=fid, fieldValues=fieldValues, weights=weights, xLocations=xLocations, yLocations=yLocations,
            profiles=profiles
        )
        samples.append(sample)
    return samples


@dataclass
class Sample(object):
    fid: int
    fieldValues: List[Any]
    weights: np.ndarray
    xLocations: np.ndarray
    yLocations: np.ndarray
    profiles: np.ndarray
