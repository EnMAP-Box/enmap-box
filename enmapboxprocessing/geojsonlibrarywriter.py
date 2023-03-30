import json
from typing import List, TextIO

from enmapbox.typeguard import typechecked
from enmapboxprocessing.typing import Number


@typechecked
class GeoJsonLibraryWriter(object):
    """A simple spectral library writer (GeoJSON format), that doesn't require QGIS API."""

    def __init__(self, file: TextIO, name='Spectral Library', description=''):
        self.file = file
        self.name = name
        self.description = description
        self.isempty = True

    def writeQml(self, file: TextIO):
        file.write(
            "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
            '<qgis>\n'
            '  <fieldConfiguration>\n'
            '    <field name="profiles">\n'
            '      <editWidget type="SpectralProfile"/>\n'
            '    </field>\n'
            '  </fieldConfiguration>\n'
            '</qgis>\n'
        )

    def initWriting(self):
        self.file.write(
            '{\n'
            '    "type": "FeatureCollection",\n'
            f'    "name": "{self.name}",\n'
            f'    "description": "{self.description}",\n'
            '    "features": [\n'
        )

    def endWriting(self):
        self.file.write(
            '\n'
            '    ]\n'
            '}\n'
        )

    def writeProfile(self, x: List[Number], y: List[Number], xUnit: str, name: str, geometry: str = None):
        if geometry is not None:
            raise NotImplementedError()

        if not self.isempty:
            self.file.write(',')
            self.file.write('\n')
        self.isempty = False

        profile = {
            "type": "Feature",
            "properties": {
                "name": name,
                "profiles": {
                    "x": x,
                    "xUnit": xUnit,
                    "y": y
                }
            },
            "geometry": None
        }
        self.file.write(' ' * 8)
        self.file.write(json.dumps(profile))
