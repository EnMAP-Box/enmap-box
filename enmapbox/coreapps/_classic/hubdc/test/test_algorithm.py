from sys import version_info
from unittest import TestCase, skipIf

import enmapboxtestdata
from _classic.hubdc.algorithm.sampling import sample_points, sample_polygons
from _classic.hubdc.core import openRasterDataset, openVectorDataset

min_version = 30000 + 600
this_version = version_info.major * 10000 + version_info.minor * 100
skiptests = this_version < min_version


@skipIf(skiptests, 'not supported in this Python version')
class Test(TestCase):

    def test_sample_points(self):
        raster = openRasterDataset(filename=enmapboxtestdata.enmap)
        vector = openVectorDataset(filename=enmapboxtestdata.landcover_points)
        samples = sample_points(raster=raster, vector=vector, idField='level_1')
        print(samples)

    def test_sample_polygons(self):
        raster = openRasterDataset(filename=enmapboxtestdata.enmap)
        vector = openVectorDataset(filename=enmapboxtestdata.landcover_points)  # lygons)
        samples = sample_polygons(raster=raster, vector=vector, fieldNames=['level_2', 'level_2_id'], oversampling=1,
                                  allTouched=False)
        for sample in samples:
            print(sample.fid, sample.fieldValues, sample.profiles.shape)

        samples = sample_polygons(raster=raster, vector=vector, fieldNames=['level_2', 'level_2_id'], oversampling=5,
                                  allTouched=False)
        for sample in samples:
            print(sample.fid, sample.fieldValues, sample.profiles.shape)

        samples = sample_polygons(raster=raster, vector=vector, fieldNames=['level_2', 'level_2_id'], oversampling=10,
                                  allTouched=False)
        for sample in samples:
            print(sample.fid, sample.fieldValues, sample.profiles.shape)
