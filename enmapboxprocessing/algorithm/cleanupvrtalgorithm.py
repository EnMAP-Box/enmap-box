import xml.etree.ElementTree as ET
from os.path import relpath, dirname
from typing import Dict, Any, List, Tuple

from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group


@typechecked
class CleanupVrtAlgorithm(EnMAPProcessingAlgorithm):
    P_VRT, _VRT = 'vrt', 'VRT file'

    def displayName(self) -> str:
        return 'Cleanup VRT file'

    def shortDescription(self) -> str:
        return 'Replaces absolute source filenames inside the VRT file with relative filenames, if possible.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._VRT, 'VRT file.'),
        ]

    def group(self):
        return Group.RasterMiscellaneous.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_VRT, self._VRT, extension='vrt')

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filename = self.parameterAsFile(parameters, self.P_VRT, context)
        cleanupVrt(filename)
        result = {}
        return result


def cleanupVrt(filename: str):
    tree = ET.parse(filename)
    root = tree.getroot()

    absoluteFilenames = list()
    for elem in root.iter("SourceFilename"):
        isRelative = elem.attrib.get("relativeToVRT") == 1
        if not isRelative:
            path = elem.text
            absoluteFilenames.append(path)

    absoluteFilenames = set(absoluteFilenames)

    with open(filename) as file:
        text = file.read()

    for absoluteFilename in absoluteFilenames:
        try:
            relativeFilename = relpath(absoluteFilename, dirname(filename))
            text = text.replace(
                'relativeToVRT="0">' + absoluteFilename,
                'relativeToVRT="1">' + relativeFilename
            )
        except ValueError:
            pass  # e.g. for ValueError: path is on mount 'c:', start on mount 'd:'

    with open(filename, 'w') as file:
        file.write(text)
