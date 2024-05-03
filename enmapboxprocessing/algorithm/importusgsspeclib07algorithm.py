from math import nan
from os import listdir
from os.path import join
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.librarydriver import LibraryDriver
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingParameterFile


@typechecked
class ImportUsgsSpeclib07Algorithm(EnMAPProcessingAlgorithm):
    P_FOLDER, _FOLDER = 'folder', 'USGS Speclib Library Version 7 folder'
    P_SPECTRAL, _SPECTRAL = 'spectral', 'Spectral characteristics'
    P_CHAPTER, _CHAPTER = 'chapter', 'Selected chapters'
    O_CHAPTER = (
        'Artificial Materials', 'Coatings', 'Liquids', 'Minerals', 'Organic Compounds', 'Soils And Mixtures',
        'Vegetation'
    )
    ArtificialMaterialsChapter, CoatingsChapter, LiquidsChapter, MineralsChapter, OrganicCompoundsChapter, \
    SoilsAndMixturesChapter, VegetationChapter = range(7)
    P_OUTPUT_LIBRARY, _OUTPUT_LIBRARY = 'outputLibrary', 'Output spectral library'

    def displayName(self):
        return 'Import USGS Spectral Library Version 7'

    def shortDescription(self):
        return 'Import the USGS Spectral Library Version 7 product.\n' \
               'As a prerequisite, download <a href="' \
               'https://www.sciencebase.gov/catalog/item/5807a2a2e4b0841e59e3a18d' \
               '">usgs_splib07.zip</a> file and unzip it.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FOLDER, 'The USGS Speclib Library Version 7 folder.'),
            (self._CHAPTER, 'Chapters to be imported. An empty selection defaults to import all chapters.'),
            (self._OUTPUT_LIBRARY, self.GpkgFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FOLDER, self._FOLDER, QgsProcessingParameterFile.Behavior.Folder)
        self.addParameterEnum(self.P_CHAPTER, self._CHAPTER, self.O_CHAPTER, True, [], True)
        self.addParameterFileDestination(self.P_OUTPUT_LIBRARY, self._OUTPUT_LIBRARY, self.GeoJsonFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        folder = self.parameterAsFile(parameters, self.P_FOLDER, context)
        chapters = self.parameterAsEnums(parameters, self.P_CHAPTER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_LIBRARY, context)

        if len(chapters) == 0:
            chapters = list(range(len(self.O_CHAPTER)))

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            folder2 = join(folder, 'ASCIIdata', 'ASCIIdata_splib07a')
            sensors = {
                'ASD': join(folder2, 'splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt'),
                'BEC': join(folder2, 'splib07a_Wavelengths_BECK_Beckman_0.2-3.0_microns.txt'),
                'AVI': join(folder2, 'splib07a_Wavelengths_AVIRIS_1996_0.37-2.5_microns.txt'),
                'NIC': join(folder2, 'splib07a_Wavelengths_NIC4_Nicolet_1.12-216microns.txt')
            }

            wavelength = dict()
            for name, filenameSensor in sensors.items():
                with open(filenameSensor) as file:
                    text = file.readlines()
                wavelength[name] = list(map(float, text[1:]))
            wavelength['NIC'] = [v / 10 for v in wavelength['NIC']]
            xUnit = 'Micrometers'

            data = []
            O_CHAPTER = [s.replace(' ', '') for s in self.O_CHAPTER]
            for chapter in listdir(folder2):

                if not chapter.startswith('Chapter'):
                    continue

                _, chapterName = chapter.split('_')

                currentChapter = O_CHAPTER.index(chapterName.replace(' ', ''))
                if currentChapter not in chapters:
                    continue

                folder3 = join(folder2, chapter)
                listdirFolder3 = listdir(folder3)
                feedback.pushInfo(f'Import {chapterName}')

                for i, spectrum in enumerate(listdirFolder3):
                    feedback.setProgress(i / len(listdirFolder3) * 100)
                    with open(join(folder3, spectrum)) as file:
                        lines = file.readlines()
                    attributes = lines[0]
                    tmp1, tmp2 = attributes.split(':')  # [1].strip()
                    name = ' '.join([s for s in tmp2.split(' ') if s != ''])
                    record = int(tmp1.split('=')[1])
                    *tmp3, sensor, ref = tmp2.strip().split(' ')
                    y = np.array(lines[1:], float)
                    y[y == -1.2300000e+034] = nan
                    x = wavelength[sensor[:3]]
                    y = list(y)
                    values = {
                        'profiles': {
                            'x': x,
                            'xUnit': xUnit,
                            'y': y
                            #                            'bbl': [1, 1, 1]
                        },
                        'name': name,
                        'chapter': chapterName,
                        'sensor': sensor,
                        'ref': ref,
                        'record': record,
                        'basename': spectrum
                    }
                    data.append(values)

            writer = LibraryDriver().createFromData('USGS Speclib Library Version 7', data)
            writer.writeToSource(filename)

            result = {self.P_OUTPUT_LIBRARY: filename}
            self.toc(feedback, result)

        return result
