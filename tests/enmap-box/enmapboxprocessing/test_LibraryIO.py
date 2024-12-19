from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsGeometry, QgsPointXY

from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import ProfileEncoding
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.libraryreader import LibraryReader
from enmapboxprocessing.testcase import TestCase


class TestLibraryIO(TestCase):

    def test_create(self):

        values = {
            'profile1': {
                'x': [1, 2, 3],
                'xUnit': 'nm',
                'y': [10, 20, 30],
                'bbl': [1, 1, 1]
            },
            'profile2': {
                'x': [1, 2, 3],
                'xUnit': 'nm',
                'y': [30, 20, 10],
                'bbl': [1, 1, 1]
            },
            'name': 'profile 1',
            'my field': 'Hello'
        }
        geometry = None

        # init library
        writer = LibraryDriver().create('My Library')
        writer.addProfileAttribute('profile1', ProfileEncoding.Text)
        writer.addProfileAttribute('profile2', ProfileEncoding.Text)
        writer.addAttribute('name', QVariant.String)
        writer.addAttribute('my field', QVariant.String)

        # add data
        writer.addFeature(values, geometry)
        # ... add more features

        # save as GeoPackage
        writer.writeToSource(self.filename('library.geojson'))

        reader = LibraryReader(writer.library)
        for values2, geometry2 in reader.data():
            self.assertEqual(values, values2)
            self.assertEqual(geometry, geometry2)

    def test_createFromData(self):

        values = {
            'profile1': {
                'x': [1, 2, 3],
                'xUnit': 'nm',
                'y': [10, 20, 30],
                'bbl': [1, 1, 1]
            },
            'profile2': {
                'x': [1, 2, 3],
                'xUnit': 'nm',
                'y': [30, 20, 10],
                'bbl': [1, 1, 1]
            },
            'name': 'profile 1',
            'my field': 'Hello'
        }
        geometry = None

        writer = LibraryDriver().createFromData([values, values])
        writer.writeToSource(self.filename('library.geojson'))

        reader = LibraryReader(writer.library)
        for values2, geometry2 in reader.data():
            self.assertEqual(values, values2)
            self.assertEqual(geometry, geometry2)

    def test_libraryWithGeometryAndCrs(self):

        values = {'my field': 'Hello'}
        geometry = QgsGeometry.fromPointXY(QgsPointXY(1, 2))

        writer = LibraryDriver().createFromData([values], [geometry])
        writer.writeToSource(self.filename('library.geojson'))

        reader = LibraryReader(writer.library)
        for values2, geometry2 in reader.data():
            self.assertEqual(values, values2)
            self.assertTrue(geometry.equals(geometry2))
