import unittest

import requests

from enmapboxprocessing.testcase import TestCase


class TestLocationBrowserApp(TestCase):

    @unittest.skipIf(TestCase.runsInCI(), 'manual tests only')
    def test_nominatim(self):
        url = 'https://nominatim.openstreetmap.org/search?q=berlin&limit=50&extratags=1&polygon_geojson=1&format=json'
        headers = {"User-Agent": "EnMAP-Box QGIS Plugin (enmapbox@enmap.org)"}  # Required user agent
        import certifi
        nominatimResults = requests.get(url, headers=headers, verify=certifi.where())
        self.assertEqual(nominatimResults.status_code, 200)
