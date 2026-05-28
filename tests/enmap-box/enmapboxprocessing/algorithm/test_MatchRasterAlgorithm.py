from os.path import basename

from enmapboxprocessing.algorithm.matchrasteralgorithm import MatchRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap_potsdam, hires_potsdom
import numpy as np

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
            alg.P_EXTRACT_PROFILE: True,
            alg.P_OUTPUT_POINTS: self.filename('dataset.geojson')
        }
        self.runalg(alg, parameters)

        d = Utils.jsonLoad(parameters[alg.P_OUTPUT_POINTS])
        self.assertEqual(len(d['features']), 2)
        p = d['features'][0]['properties']
        p['match-source'] = basename(p['match-source'])
        profile = p.pop('match-profile')
        self.assertEqual(round(profile['y'][0], 5), 0.0125)
        self.assertEqual(profile['x'][0], 418.24)

        gold = {
            'date': '2027-01-01', 'fid': 32, 'level_1': 'vegetation', 'level_2': 'low vegetation',
            'match-px': 286, 'match-py': 171, 'match-source': 'enmap_potsdam.tif', 'match-dt': -365
        }
        self.assertDictEqual(gold, p)
        p = d['features'][1]['properties']
        p['match-source'] = basename(p['match-source'])
        profile = p.pop('match-profile')
        gold = {
            'fid': 73, 'level_1': 'vegetation', 'level_2': 'tree', 'date': '2027-01-01',
            'match-source': 'aerial_potsdam.tif', 'match-px': 938, 'match-py': 5101, 'match-dt': 0
        }
        self.assertEqual(gold, p)

    def test_max_dt(self):
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

        d = Utils.jsonLoad(parameters[alg.P_OUTPUT_POINTS])
        self.assertEqual(len(d['features']), 2)
        p = d['features'][0]['properties']
        p['match-source'] = basename(p['match-source'])
        p.pop('match-profile')
        gold = {
            'date': '2027-01-01', 'fid': 32, 'level_1': 'vegetation', 'level_2': 'low vegetation',
            'match-px': -1, 'match-py': -1, 'match-source': '', 'match-dt': -1
        }
        self.assertDictEqual(gold, p)
        p = d['features'][1]['properties']
        p['match-source'] = basename(p['match-source'])
        p.pop('match-profile')
        gold = {
            'fid': 73, 'level_1': 'vegetation', 'level_2': 'tree', 'date': '2027-01-01',
            'match-source': 'aerial_potsdam.tif', 'match-px': 938, 'match-py': 5101, 'match-dt': 0
        }
        self.assertEqual(gold, p)
