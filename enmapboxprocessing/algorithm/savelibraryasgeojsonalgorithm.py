from typing import Dict, Any, List, Tuple

from enmapbox.qgispluginsupport.qps.speclib.core import profile_field_list
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import SpectralProfile
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsFeature)
from typeguard import typechecked


@typechecked
class SaveLibraryAsGeoJsonAlgorithm(EnMAPProcessingAlgorithm):
    P_LIBRARY, _LIBRARY = 'library', 'Spectral library'
    P_OUTPUT_FILE, _OUTPUT_FILE = 'outputFile', 'Output file'

    @classmethod
    def displayName(cls) -> str:
        return 'Save spectral library as GeoJSON file'

    def shortDescription(self) -> str:
        return 'Save a spectral library as a human-readable GeoJSON text file. ' \
               'All binary profile fields will be converted into human-readable dictionary strings.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._LIBRARY, 'The spectral library to be stored as GeoJSON text file.'),
            (self._OUTPUT_FILE, 'Destination GeoJSON file.')
        ]

    def group(self):
        return Group.Test.value + Group.ExportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_LIBRARY, self._LIBRARY)
        self.addParameterFileDestination(self.P_OUTPUT_FILE, self._OUTPUT_FILE, 'GeoJSON (*.geojson)')

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        library = self.parameterAsVectorLayer(parameters, self.P_LIBRARY, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FILE, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # save as GeoJSON
            alg = 'native:savefeatures'
            parameters = {'INPUT': library, 'OUTPUT': filename}
            self.runAlg(alg, parameters, None, feedback2, context, True)

            # repair SpectralProfile attributes
            data = Utils.jsonLoad(filename)
            assert len(data['features']) == library.featureCount()

            profileFields = profile_field_list(library)

            n = library.featureCount()
            feature: QgsFeature
            for i, feature in enumerate(library.getFeatures()):
                feedback.setProgress(i / n * 100)
                for field in profileFields:
                    spectralProfile = SpectralProfile.fromQgsFeature(feature, field)
                    data['features'][i]['properties'][field.name()] = spectralProfile.values()

            Utils.jsonDump(data, filename)

            result = {self.P_OUTPUT_FILE: filename}
            self.toc(feedback, result)
        return result
