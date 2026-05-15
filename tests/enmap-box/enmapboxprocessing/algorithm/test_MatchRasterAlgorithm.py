from enmapboxprocessing.algorithm.matchrasteralgorithm import MatchRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap_potsdam, hires_potsdom


class TestMatchRasterAlgorithm(TestCase):

    def test(self):
        timeseries = self.filename('timeseries.txt')
        with open(timeseries, 'w') as file:
            file.write(
                'raster,mask,date\n'
                f'{enmap_potsdam},,2026-01-01\n'
                f'{hires_potsdom},,2027-01-01\n'
            )

        poi = self.filename('poi.geojson')
        with open(poi, 'w') as file:
            file.write(
                '{\n'
                '    "type": "FeatureCollection",\n'
                '    "name": "poi",\n'
                '    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::32633" } },\n'
                '    "features": [\n'
                '        { "type": "Feature", "properties": { "fid": 32, "level_1": "vegetation", "level_2": "low vegetation", "date": "2027-01-01" }, "geometry": { "type": "Point", "coordinates": [ 370775.181699999608099, 5804816.683299999684095 ] } },\n'
                '        { "type": "Feature", "properties": { "fid": 73, "level_1": "vegetation", "level_2": "tree", "date": "2027-01-01" }, "geometry": { "type": "Point", "coordinates": [ 365009.064299999736249, 5806845.435200000181794 ] } }\n'
                '    ]\n'
                '}'
            )

        alg = MatchRasterAlgorithm()
        parameters = {
            alg.P_TIMESERIES: timeseries,
            alg.P_POI: poi,
            alg.P_DATE_FIELD: 'date',
            alg.P_MAXIMUM_TEMPORAL_OFFSET: 0,
            alg.P_OUTPUT_POINTS: self.filename('dataset.geojson')
        }
        self.runalg(alg, parameters)
