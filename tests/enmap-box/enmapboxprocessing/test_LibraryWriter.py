from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.testcase import TestCase
from qgis.PyQt.QtCore import QVariant
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import ProfileEncoding


class TestLibraryWriter(TestCase):

    def test(self):
        start_app()
        initAll()

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
        writer.addAttribute('my field', QVariant.String)

        # add data
        writer.addFeature(values, geometry)
        # ... add more features

        # save as GeoPackage
        writer.writeToSource(self.filename('library.gpkg'))

    def test2(self):
        start_app()
        initAll()

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

        writer = LibraryDriver().createFromData('My Library', [values, values])
        writer.writeToSource(self.filename('library2.gpkg'))
