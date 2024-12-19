import unittest

from osgeo import gdal

from enmapboxprocessing.algorithm.samplerastervaluesalgorithm import SampleRasterValuesAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap, landcover_polygon, hires_potsdom
from enmapboxtestdata import landcover_points_singlepart_epsg3035
from qgis.core import (QgsRasterLayer, QgsVectorLayer)


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestSampleRasterValuesAlgorithm(TestCase):

    def test_sampleFromVectorPoints(self):
        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_VECTOR: landcover_points_singlepart_epsg3035,
            alg.P_OUTPUT_POINTS: self.filename('sample_vectorPoint.gpkg')
        }
        result = self.runalg(alg, parameters)

    def test_sampleFromVectorPolygons(self):
        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_VECTOR: QgsVectorLayer(landcover_polygon),
            alg.P_OUTPUT_POINTS: self.filename('sample_vectorPolygons.gpkg')

        }
        result = self.runalg(alg, parameters)

    def test_coverageRange(self):
        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_COVERAGE_RANGE: [70, 100],
            alg.P_OUTPUT_POINTS: self.filename('sample_70p_pure.gpkg')

        }
        result = self.runalg(alg, parameters)
        points = QgsVectorLayer(result[alg.P_OUTPUT_POINTS])
        self.assertEqual(404, points.featureCount())
        self.assertListEqual(
            ['fid', 'COVER', 'level_1_id', 'level_1', 'level_2_id', 'level_2', 'level_3_id', 'level_3'],
            points.fields().names()[:8]
        )

    def test_skipNoDataPixel(self):
        # create locations: one inside, one outside of the valid data region
        locations = self.filename('locations.geojson')
        with open(locations, 'w') as file:
            file.write(
                '''{
                    "type": "FeatureCollection",
                    "name": "points",
                    "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                    "features": [
                        {"type": "Feature", "properties": {},
                         "geometry": {"type": "Point", "coordinates": [13.052692126870632, 52.430044161016681]}},
                        {"type": "Feature", "properties": {},
                         "geometry": {"type": "Point", "coordinates": [13.047895332769757, 52.401654271016177]}}
                    ]
                }'''
            )

        alg = SampleRasterValuesAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: hires_potsdom,
            alg.P_VECTOR: locations,
            alg.P_SKIP_NO_DATA_PIXEL: True,
            alg.P_OUTPUT_POINTS: self.filename('sample.gpkg')

        }
        result = self.runalg(alg, parameters)
        points = QgsVectorLayer(result[alg.P_OUTPUT_POINTS])
        self.assertEqual(1, points.featureCount())
