from math import nan
from os import listdir
from os.path import join
from typing import Dict, Any, List, Tuple

import numpy as np
from qgis.core import QgsVectorLayer, QgsMapLayer, QgsProcessingContext, QgsProcessingFeedback, \
    QgsProcessingParameterFile

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.librarydriver import LibraryDriver


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
        'Beckman 5270 (0.2 to 3 µm)', 'hi-resNG ASD (0.35 to 2.5 µm)', 'Nicolet FTIR (1 to 216 µm)',
        'AVIRIS (0.37 to 2.5 µm)'
    )
    AllSpectrometers = BeckmanSpectrometer, AsdSpectrometer, NicoletSpectrometer, AvirisSpectrometer = list(range(4))
    P_SPECTRAL_CHARACTERISTIC, _SPECTRAL_CHARACTERISTIC = 'spectralCharacteristic', 'Spectral characteristic'
    O_SPECTRAL_CHARACTERISTIC = (
        'original sampling positions',
        'oversampled cubic-spline interpolation',
        'cvASD – ASD spectrometer',
        'cvAVIRISc1995 – AVIRIS-Classic 1995',
        'cvAVIRISc1996 – AVIRIS-Classic 1996',
        'cvAVIRISc1997 – AVIRIS-Classic 1997',
        'cvAVIRISc1998 – AVIRIS-Classic 1998',
        'cvAVIRISc1999 – AVIRIS-Classic 1999',
        'cvAVIRISc2000 – AVIRIS-Classic 2000',
        'cvAVIRISc2001 – AVIRIS-Classic 2001',
        'cvAVIRISc2005 – AVIRIS-Classic 2005',
        'cvAVIRISc2006 – AVIRIS-Classic 2006',
        'cvAVIRISc2009 – AVIRIS-Classic 2009',
        'cvAVIRISc2010 – AVIRIS-Classic 2010',
        'cvAVIRISc2011 – AVIRIS-Classic 2011',
        'cvAVIRISc2012 – AVIRIS-Classic 2012',
        'cvAVIRISc2013 – AVIRIS-Classic 2013',
        'cvAVIRISc2014 – AVIRIS-Classic 2014',
        'cvHYMAP2007 – HyMap 2007',
        'cvHYMAP2014 – HyMap 2014',
        'cvHYPERION - Hyperion',
        'cvVIMS – Cassini VIMS',
        'cvCRISM-global – Mars Reconnaissance Orbiter CRISM (global mode)',
        'cvCRISMjMTR3 – Mars Reconnaissance Orbiter CRISM (targeted mode)',
        'cvM3-target – Moon Mineralogy Mapper',
        'rsASTER – ASTER',
        'rsLandsat8 – Landsat-8 OLI',
        'rsSentinel2 – Sentinel-2 MSI',
        'rsWorldView3 – WorldView3'
    )
    AllCharacteristics = (
        OriginalSamplingPositionsCharacteristic,
        OversampledCubicSplineInterpolationCharacteristic,
        ASDCharacteristic,
        AVIRIS1995Characteristic,
        AVIRIS1996Characteristic,
        AVIRIS1997Characteristic,
        AVIRIS1998Characteristic,
        AVIRIS1999Characteristic,
        AVIRIS2000Characteristic,
        AVIRIS2001Characteristic,
        AVIRIS2005Characteristic,
        AVIRIS2006Characteristic,
        AVIRIS2009Characteristic,
        AVIRIS2010Characteristic,
        AVIRIS2011Characteristic,
        AVIRIS2012Characteristic,
        AVIRIS2013Characteristic,
        AVIRIS2014Characteristic,
        HyMap2007Characteristic,
        HyMap2014Characteristic,
        HyperionCharacteristic,
        CassiniVIMSCharacteristic,
        CRISMGlobalModeCharacteristic,
        CRISMTargetedModeCharacteristic,
        MoonMineralogyMapperCharacteristic,
        ASTERCharacteristic,
        Landsat8OLICharacteristic,
        Sentinel2MSICharacteristic,
        WorldView3Characteristic
    ) = list(range(29))
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
            (self._SPECTRAL_CHARACTERISTIC, 'Select spectral output characteristic.'),
            (self._OUTPUT_LIBRARY, self.GpkgFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FOLDER, self._FOLDER, QgsProcessingParameterFile.Behavior.Folder)
        self.addParameterEnum(self.P_CHAPTER, self._CHAPTER, self.O_CHAPTER, True, None, False)
        self.addParameterEnum(self.P_SPECTROMETER, self._SPECTROMETER, self.O_SPECTROMETER, True, None, False)
        self.addParameterEnum(
            self.P_SPECTRAL_CHARACTERISTIC, self._SPECTRAL_CHARACTERISTIC, self.O_SPECTRAL_CHARACTERISTIC, False,
            self.OriginalSamplingPositionsCharacteristic, False
        )
        self.addParameterFileDestination(self.P_OUTPUT_LIBRARY, self._OUTPUT_LIBRARY, self.GeoJsonFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        folder = self.parameterAsFile(parameters, self.P_FOLDER, context)
        selectedChapters = self.parameterAsEnums(parameters, self.P_CHAPTER, context)
        selectedSensors = self.parameterAsEnums(parameters, self.P_SPECTROMETER, context)
        selectedCharacteristic = self.parameterAsEnum(parameters, self.P_SPECTRAL_CHARACTERISTIC, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_LIBRARY, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)
            if selectedCharacteristic == self.OriginalSamplingPositionsCharacteristic:
                folder2 = join(folder, 'ASCIIdata', 'ASCIIdata_splib07a')
                sensors = {
                    'BEC': join(folder2, 'splib07a_Wavelengths_BECK_Beckman_0.2-3.0_microns.txt'),
                    'ASD': join(folder2, 'splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt'),
                    'NIC': join(folder2, 'splib07a_Wavelengths_NIC4_Nicolet_1.12-216microns.txt'),
                    'AVI': join(folder2, 'splib07a_Wavelengths_AVIRIS_1996_0.37-2.5_microns.txt'),
                }

            elif selectedCharacteristic == self.OversampledCubicSplineInterpolationCharacteristic:
                folder2 = join(folder, 'ASCIIdata', 'ASCIIdata_splib07b')
                sensors = {
                    'BEC': join(folder2, 'splib07b_Wavelengths_BECK_Beckman_interp._3961_ch.txt'),
                    'ASD': join(folder2, 'splib07b_Wavelengths_ASDFR_0.35-2.5microns_2151ch.txt'),
                    'NIC': join(folder2, 'splib07b_Wavelengths_NIC4_Nicolet_1.12-216microns.txt'),
                    'AVI': join(folder2, 'splib07b_Wavelengths_AVIRIS_1996_interp_to_2203ch.txt'),
                }
            else:
                folder2 = join(folder, 'ASCIIdata', 'ASCIIdata_splib07b_')
                folder2 += self.O_SPECTRAL_CHARACTERISTIC[selectedCharacteristic].split(' ')[0]
                # find wavelength file
                for entry in listdir(folder2):
                    if 'wavelength' in entry.lower() and entry.endswith('.txt'):
                        sensors = {'': join(folder2, entry)}
                    if 'waves' in entry.lower() and entry.endswith('.txt'):  # special case for AVIRIS 2010
                        sensors = {'': join(folder2, entry)}
                if selectedCharacteristic == self.ASTERCharacteristic:
                    sensors[''] = join(folder2, 'S07ASTER_Wavelengths_ASTER_(9_bands)_microns.txt')  # fix ASTER
                if selectedCharacteristic == self.WorldView3Characteristic:
                    sensors[''] = join(folder2, 'S07WV3_Wavelengths_WorldView3_(16_bands)_micron.txt')  # fix WV3

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
                wavelength[name] = [float(v) for v in text[1:]]
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
                    if '' in wavelength:
                        x = wavelength['']
                    else:
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
