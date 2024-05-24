from os.path import splitext

from enmapboxprocessing.geojsonlibrarywriter import GeoJsonLibraryWriter
from enmapboxprocessing.testcase import TestCase
from enmapboxprocessing.utils import Utils


class TestGeoJsonLibraryWriter(TestCase):

    def test(self):
        filename = self.filename('library.geojson')
        with open(filename, 'w') as file1, open(splitext(filename)[0] + '.qml', 'w') as file2:
            writer = GeoJsonLibraryWriter(file1, 'My Library', '')
            writer.initWriting()

            name = 'profile 1'
            properties = {'field 1': 1}
            x = [1, 2, 3]
            y = [10, 20, 30]
            bbl = [0, 1, 1]

            writer.writeProfile(x, y, bbl, 'Nanometers', name, None, properties)
            writer.endWriting()
            writer.writeQml(file2)

        lead = str(Utils().jsonLoad(filename))
        gold = "{'type': 'FeatureCollection', 'name': 'My Library', 'description': '', 'features': [{'type': 'Feature', 'properties': {'name': 'profile 1', 'profiles': {'x': [1, 2, 3], 'xUnit': 'Nanometers', 'y': [10, 20, 30], 'bbl': [0, 1, 1]}, 'field 1': 1}, 'geometry': None}]}"
        self.assertEqual(gold, lead)
