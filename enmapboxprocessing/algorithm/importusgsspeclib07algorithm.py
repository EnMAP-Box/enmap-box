from math import nan
from os import listdir
from os.path import join
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.librarydriver import LibraryDriver
from qgis.core import QgsVectorLayer, QgsMapLayer, QgsProcessingContext, QgsProcessingFeedback, \
    QgsProcessingParameterFile


@typechecked
class ImportUsgsSpeclib07Algorithm(EnMAPProcessingAlgorithm):
    P_FOLDER, _FOLDER = 'folder', 'USGS Speclib Library Version 7 folder'
    P_CHAPTER, _CHAPTER = 'chapter', 'Selected chapters'
    O_CHAPTER = (
        'Artificial Materials', 'Coatings', 'Liquids', 'Minerals', 'Organic Compounds', 'Soils And Mixtures',
        'Vegetation'
    )
    AllChapters = (
        ArtificialMaterialsChapter, CoatingsChapter, LiquidsChapter, MineralsChapter, OrganicCompoundsChapter,
        SoilsAndMixturesChapter, VegetationChapter) = list(range(7))
    P_SPECTROMETER, _SPECTROMETER = 'spectrometer', 'Selected spectrometers'
    O_SPECTROMETER = (
        'Beckman 5270 (0.2 to 3 µm)', 'hi-resNG ASD (0.35 to 2.5 µm', 'Nicolet FTIR (0.1 to 21.6 µm',
        'AVIRIS (0.37 to 2.5 µm)'
    )
    AllSpectrometers = BeckmanSpectrometer, AsdSpectrometer, NicoletSpectrometer, AvirisSpectrometer = list(range(4))
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
            (self._CHAPTER, 'Filter spectra to be imported by chapter.'),
            (self._SPECTROMETER, 'Filter spectra to be imported by spectrometer.'),
            (self._OUTPUT_LIBRARY, self.GpkgFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FOLDER, self._FOLDER, QgsProcessingParameterFile.Behavior.Folder)
        self.addParameterEnum(self.P_CHAPTER, self._CHAPTER, self.O_CHAPTER, True)
        self.addParameterEnum(self.P_SPECTROMETER, self._SPECTROMETER, self.O_SPECTROMETER, True)
        self.addParameterFileDestination(self.P_OUTPUT_LIBRARY, self._OUTPUT_LIBRARY, self.GeoJsonFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        folder = self.parameterAsFile(parameters, self.P_FOLDER, context)
        selectedChapters = self.parameterAsEnums(parameters, self.P_CHAPTER, context)
        selectedSensors = self.parameterAsEnums(parameters, self.P_SPECTROMETER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_LIBRARY, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            folder2 = join(folder, 'ASCIIdata', 'ASCIIdata_splib07a')
            sensors = {
                'BEC': join(folder2, 'splib07a_Wavelengths_BECK_Beckman_0.2-3.0_microns.txt'),
                'ASD': join(folder2, 'splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt'),
                'NIC': join(folder2, 'splib07a_Wavelengths_NIC4_Nicolet_1.12-216microns.txt'),
                'AVI': join(folder2, 'splib07a_Wavelengths_AVIRIS_1996_0.37-2.5_microns.txt'),
            }
            sensorIds = {
                'BEC': self.BeckmanSpectrometer,
                'ASD': self.AsdSpectrometer,
                'NIC': self.NicoletSpectrometer,
                'AVI': self.AvirisSpectrometer,
            }

            wavelength = dict()
            for name, filenameSensor in sensors.items():
                with open(filenameSensor) as file:
                    text = file.readlines()
                factor = 0.1 if name == 'NIC' else 1
                wavelength[name] = [float(v) * factor for v in text[1:]]
            xUnit = 'Micrometers'

            data = []
            O_CHAPTER = [s.replace(' ', '') for s in self.O_CHAPTER]
            for chapter in listdir(folder2):

                if not chapter.startswith('Chapter'):
                    continue

                _, chapterName = chapter.split('_')

                currentChapter = O_CHAPTER.index(chapterName.replace(' ', ''))
                if currentChapter not in selectedChapters:
                    continue

                folder3 = join(folder2, chapter)
                listdirFolder3 = listdir(folder3)
                feedback.pushInfo(f'Import {chapterName}')

                for i, spectrum in enumerate(listdirFolder3):
                    feedback.setProgress(i / len(listdirFolder3) * 100)
                    with open(join(folder3, spectrum)) as file:
                        lines = file.readlines()
                    attributes = lines[0]
                    tmp1, tmp2 = attributes.split(':')
                    name = ' '.join([s for s in tmp2.split(' ') if s != ''])
                    record = int(tmp1.split('=')[1])
                    *tmp3, sensor, ref = tmp2.strip().split(' ')
                    html = '_'.join([s for s in tmp2.strip().split(' ') if s != ''])
                    html = html.replace('<', 'lt').replace('/', '-').replace('>', 'gt')
                    html = join(folder, 'HTMLmetadata', html + '.html')
                    sensorKey = sensor[:3]
                    sensorId = sensorIds[sensorKey]
                    if sensorId not in selectedSensors:
                        continue
                    y = np.array(lines[1:], float)
                    y[y == -1.2300000e+034] = nan
                    x = wavelength[sensorKey]
                    y = list(y)
                    values = {
                        'profiles': {
                            'x': x,
                            'xUnit': xUnit,
                            'y': y
                            #                            'bbl': [1, 1, 1]
                        },
                        'name': name,
                        'html': html,
                        'chapter': chapterName,
                        'sensor': sensor,
                        'ref': ref,
                        'record': record,
                        'basename': spectrum
                    }
                    data.append(values)

            writer = LibraryDriver().createFromData(data, None, 'USGS Speclib Library Version 7')
            writer.writeToSource(filename)
            library = QgsVectorLayer(filename)
            library.loadNamedStyle(__file__.replace('.py', '.qml'))
            library.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_LIBRARY: filename}
            self.toc(feedback, result)

        return result

    """def parseDataTable(self, htmlFilename: str):
        with open(htmlFilename) as file:
            text = file.readlines()

        itemIndices = []
        for i, line in enumerate(text):
            if line.startswith('<TR><TD scope="row">'):
                itemIndices.append()

        titles = []

        for i in itemIndices:


        description
        asciiSpectrum
        asciiSpectrumErrorBars
        asciiWavelengths
        asciiBandpass
            <TH scope="col"><B>GIF Wavelengths (&#181;m) Plot</B></TH>
     <TH scope="col"><B>GIF Bandpass (&#181;m) Plot</B></TH>"""
