from _classic.hubdc.core2 import *
import fnmatch

LANDSAT_SENSORS = ('LND04', 'LND05', 'LND07', 'LND08')
LANDSAT4, LANDSAT5, LANDSAT7, LANDSAT8 = LANDSAT_SENSORS
SENTINEL2_SENSORS = ('SEN2A', 'SEN2B')
SENTINEL2A, SENTINEL2B = SENTINEL2_SENSORS

(BAND_Blue, BAND_Green, BAND_Red, BAND_RedEdge1, BAND_RedEdge2, BAND_RedEdge3, BAND_PANNearInfrared, BAND_NearInfrared,
BAND_ShortwaveInfrared1, BAND_ShortwaveInfrared2, BAND_QualityAssuranceInformation, BAND_AerosolOpticalDepth,
BAND_CloudAndCloudShadowDistance, BAND_WaterVapor, BAND_ViewZenith, BAND_HazeOptimizedTransformation) = \
    ('BLUE', 'GREEN', 'RED', 'RE1', 'RE2', 'RE3', 'PNIR', 'NIR', 'SWIR1', 'SWIR2', 'QAI', 'AOD', 'CLD', 'WV',
     'VZN', 'HOT')

LANDSAT_BOA_BANDS = (BAND_Blue, BAND_Green, BAND_Red, BAND_PANNearInfrared, BAND_NearInfrared, BAND_ShortwaveInfrared1,
                     BAND_ShortwaveInfrared2)

SENTINEL2_BOA_BANDS = (BAND_Blue, BAND_Green, BAND_Red, BAND_RedEdge1, BAND_RedEdge2, BAND_RedEdge3,
                       BAND_PANNearInfrared, BAND_NearInfrared, BAND_ShortwaveInfrared1, BAND_ShortwaveInfrared2)

def sentinel2Raster(folder, date, sensor, ext, geometry, tilingScheme):
    raster = Raster(name='{}_{}'.format(date, sensor), date=date)
    for subproduct, bands, names in [('BOA', 10, SENTINEL2_BOA_BANDS),
                                     ('CLD', 1, [BAND_CloudAndCloudShadowDistance]),
                                     ('HOT', 1, [BAND_HazeOptimizedTransformation]),
                                     ('QAI', 1, [BAND_QualityAssuranceInformation]),
                                     ('VZN', 1, [BAND_ViewZenith])]:

        filename = join(folder, '{}_LEVEL2_{}_{}{}'.format(date, sensor, subproduct, ext))
        for index in range(bands):

            if subproduct == 'BOA':
                wavelength = [0.492, 0.560, 0.665, 0.704, 0.740, 0.783, 0.833, 0.865, 1.614, 2.202][index] * 1000
            else:
                wavelength = None

            raster.addBand(band=Band(filename=filename, index=index, mask=None, name=names[index], date=date,
                                     wavelength=wavelength, geometry=geometry, tilingScheme=tilingScheme))

    mask = raster.select(BAND_QualityAssuranceInformation).not_equal(1)
    raster = raster.updateMask(mask=mask)
    return raster

def landsatRaster(folder, date, sensor, ext, geometry, tilingScheme):
    assert sensor in LANDSAT_SENSORS
    raster = Raster(name='{}_{}'.format(date, sensor), date=date)
    for subproduct, bands, names in [('BOA', 6, LANDSAT_BOA_BANDS),
                                     ('CLD', 1, [BAND_CloudAndCloudShadowDistance]),
                                     ('HOT', 1, [BAND_HazeOptimizedTransformation]),
                                     ('QAI', 1, [BAND_QualityAssuranceInformation]),
                                     ('VZN', 1, [BAND_ViewZenith])]:
        filename = join(folder, '{}_LEVEL2_{}_{}{}'.format(date, sensor, subproduct, ext))
        for index in range(bands):

            if subproduct == 'BOA':
                wavelength = {LANDSAT4: [0.486, 0.571, 0.659, 0.839, 1.679, 2.217],
                              LANDSAT5: [0.486, 0.570, 0.660, 0.838, 1.677, 2.217],
                              LANDSAT7: [0.478, 0.561, 0.661, 0.834, 1.650, 2.208],
                              LANDSAT8: [0.482, 0.561, 0.654, 0.864, 1.609, 2.201]}[sensor][index] * 1000
            else:
                wavelength = None

            raster.addBand(band=Band(filename, index=index, mask=None, name=names[index], date=date,
                                     wavelength=wavelength, geometry=geometry, tilingScheme=tilingScheme))

    mask = raster.select(BAND_QualityAssuranceInformation).not_equal(1).cache()
    raster = raster.updateMask(mask=mask)
    return raster


tilingScheme = TilingScheme()
tilingScheme.addTile(Tile(name='X0069_Y0043',
                          extent=Extent(xmin=4526026.0, xmax=4556026.0, ymin=3254919.5, ymax=3284919.5,
                                        projection=Projection(wkt='PROJCS["ETRS89/LAEAEurope",GEOGCS["ETRS89",DATUM["European_Terrestrial_Reference_System_1989",SPHEROID["GRS1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6258"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4258"]],PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["latitude_of_center",52],PARAMETER["longitude_of_center",10],PARAMETER["false_easting",4321000],PARAMETER["false_northing",3210000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3035"]]'))))
tilingScheme.addTile(Tile(name='X0070_Y0043',
                     extent=Extent(xmin=4556026.0, xmax=4586026.0, ymin=3254919.5, ymax=3284919.5,
                                   projection=Projection(wkt='PROJCS["ETRS89/LAEAEurope",GEOGCS["ETRS89",DATUM["European_Terrestrial_Reference_System_1989",SPHEROID["GRS1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6258"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4258"]],PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["latitude_of_center",52],PARAMETER["longitude_of_center",10],PARAMETER["false_easting",4321000],PARAMETER["false_northing",3210000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3035"]]'))))

#tilingScheme = TilingSchemeFile(filename=r'C:\Work\data\FORCE\tiling_scheme\europe_3035.shp', )


def collections(folder, ext):
    sensors = LANDSAT_SENSORS + SENTINEL2_SENSORS
    rasters = {sensor: dict() for sensor in sensors}
    geometries = {sensor: dict() for sensor in sensors}
    patterns = {sensor: '*_LEVEL2_{}_BOA{}'.format(sensor, ext) for sensor in sensors}
    for tile in tilingScheme.tiles():
        extent = tile.extent()
        for filename in listdir(join(folder, tile.name())):
            for sensor in sensors:
                if fnmatch.fnmatch(filename, patterns[sensor]):
                    date = filename[:8]
                    key = date
                    if key not in rasters[sensor]:
                        if sensor in LANDSAT_SENSORS:
                            raster = landsatRaster(folder=folder, date=Date.parse(date), sensor=sensor, ext=ext, geometry=None, tilingScheme=tilingScheme)
                        elif sensor in SENTINEL2_SENSORS:
                            raster = sentinel2Raster(folder=folder, date=Date.parse(date), sensor=sensor, ext=ext, geometry=None, tilingScheme=tilingScheme)
                        else:
                            assert 0
                        rasters[sensor][key] = raster
                    if key in geometries[sensor]:
                        geometries[sensor][key] = extent.union(other=geometries[sensor][key])
                    else:
                        geometries[sensor][key] = extent

    for sensor in rasters:
        for key, raster in rasters[sensor].items():
            for band in raster.bands():
                band.setGeometry(geometries[sensor][key])

    collections = list()
    for sensor in sensors:
        collection = Collection()
        collection._rasters = list(rasters[sensor].values())
        collections.append(collection)

    class L2Collections(object):
        def __init__(self, collections):
            self._collections = collections

        def _get(self, i):
            c = self._collections[i]
            assert isinstance(c, Collection)
            return c

        def __iter__(self):
            for c in self._collections:
                assert isinstance(c, Collection)
                yield c

        @property
        def l4(self):
            return self._get(0)

        @property
        def l5(self):
            return self._get(1)

        @property
        def l7(self):
            return self._get(2)

        @property
        def l8(self):
            return self._get(3)

        @property
        def s2(self):
            return self._get(4)

    return L2Collections(collections)