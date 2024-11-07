import requests
from enmapboxprocessing.testcase import TestCase

class LocationBrowserApp(TestCase):

    def test_nominatim(self):
        url = 'https://nominatim.openstreetmap.org/search?q=berlin&limit=50&extratags=1&polygon_geojson=1&format=json'
        headers = {"User-Agent": "EnMAP-Box QGIS Plugin (enmapbox@enmap.org)"}  # Required user agent
        nominatimResults = requests.get(url, headers=headers)
        self.assertEqual(nominatimResults.status_code, 200)
