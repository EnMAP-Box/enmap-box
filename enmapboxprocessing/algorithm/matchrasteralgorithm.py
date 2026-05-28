from typing import Dict, Any, List, Tuple

import numpy as np
from qgis.PyQt.QtCore import QDate
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent, SpatialPoint
from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils


@typechecked
class MatchRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_TIMESERIES, _TIMESERIES = 'timeSeries', 'Time series'
    P_POI, _POI = 'poi', 'Points of interest'
    P_DATE_FIELD, _DATE_FIELD = 'dateField', 'Date field'
    P_MAXIMUM_TEMPORAL_OFFSET, _MAXIMUM_TEMPORAL_OFFSET = 'maximumTemporalOffset', 'Maximum temporal offset (days)'
    P_EXTRACT_PROFILE, _EXTRACT_PROFILE = 'extractProfile', 'Extract pixel profiles'
    P_OUTPUT_POINTS, _OUTPUT_POINTS = 'outputPoints', 'Output point layer'

    def displayName(self) -> str:
        return 'Match raster timeseries with points of interest'

    def shortDescription(self) -> str:
        return ('Creates a new point layer containing the attributes of the input layer together with raster matching '
                'information for the pixel covered by each point and temporally closest to the target date. The output '
                'includes the raster source (match-source), pixel coordinates (match-px, match-py), the extracted '
                'pixel profile (match-profile), and the temporal offset to the target date (match-dt).')

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._TIMESERIES, 'A time series to sample data from.'),
            (self._POI, 'A vector point layer defining the locations to match and sample.'),
            (self._DATE_FIELD, 'Field with target date.'),
            (self._MAXIMUM_TEMPORAL_OFFSET, 'Maximum allowed gap in days, '
                                            'between target date and image acquisition date'),
            (self._EXTRACT_PROFILE, 'Whether to extract pixel profiles.'),
            (self._OUTPUT_POINTS, self.VectorFileDestination)
        ]

    def group(self):
        return Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_TIMESERIES, self._TIMESERIES)
        self.addParameterVectorLayer(self.P_POI, self._POI)
        self.addParameterField(self.P_DATE_FIELD, self._DATE_FIELD, None, self.P_POI)
        self.addParameterInt(self.P_MAXIMUM_TEMPORAL_OFFSET, self._MAXIMUM_TEMPORAL_OFFSET, None, True, 0)
        self.addParameterBoolean(self.P_EXTRACT_PROFILE, self._EXTRACT_PROFILE, False, True)
        self.addParameterVectorDestination(self.P_OUTPUT_POINTS, self._OUTPUT_POINTS)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        timeseries = self.parameterAsFile(parameters, self.P_TIMESERIES, context)
        poi = self.parameterAsVectorLayer(parameters, self.P_POI, context)
        dateField = self.parameterAsField(parameters, self.P_DATE_FIELD, context)
        dateFieldIndex = poi.fields().indexFromName(dateField)
        maxTempOffset = self.parameterAsInt(parameters, self.P_MAXIMUM_TEMPORAL_OFFSET, context)
        extractProfiles = self.parameterAsBoolean(parameters, self.P_EXTRACT_PROFILE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_POINTS, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            pointInfos = list()
            geometries = list()
            dateFirst = QDate(9999, 1, 1)
            dateLast = QDate(0, 1, 1)

            for feature in poi.getFeatures():
                point = feature.geometry().asPoint()
                attributes = feature.attributes()
                date = attributes[dateFieldIndex]
                pointInfos.append((point, attributes, date))
                geometries.append(feature.geometry())
                dateFirst = min(dateFirst, date)
                dateLast = max(dateLast, date)

            with open(timeseries, 'r') as file:
                lines = file.readlines()

            rasterInfos = list()
            rasterDates = list()
            for i, line in enumerate(lines):
                raster, mask, date = line.strip().split(',')
                if i == 0:
                    assert raster == 'raster'
                    assert mask == 'mask'
                    assert date == 'date'
                    continue
                if mask == '':
                    mask = raster

                rasterReader = RasterReader(raster)
                maskReader = RasterReader(mask)
                date = Utils.parseDateTime(date).date()
                extent = SpatialExtent.fromLayer(rasterReader.layer).toCrs(poi.crs())

                # filter by dates
                if maxTempOffset is not None:
                    if date.addDays(maxTempOffset) < dateFirst:
                        continue
                    if date.addDays(-1 * maxTempOffset) > dateLast:
                        continue

                # filter by extent
                if not extent.intersects(poi.extent()):
                    continue

                rasterInfos.append((rasterReader, maskReader, date, extent))
                rasterDates.append(date)

            # match raster with points
            rasterReader: RasterReader
            maskReader: RasterReader
            fieldNames = poi.fields().names()
            data = list()
            for point, attributes, targetDate in pointInfos:

                # sort by distance to target date
                sortedIndices = sorted(
                    range(len(rasterDates)),
                    key=lambda i: abs(rasterDates[i].daysTo(targetDate))
                )

                # find first valid match
                found = False
                for index in sortedIndices:
                    rasterReader, maskReader, date, extent = rasterInfos[index]
                    attributesDict = dict(zip(fieldNames, attributes))

                    # filter by mask
                    pointInMaskCrs = SpatialPoint(poi.crs(), point).toCrs(maskReader.crs())
                    pixel = maskReader.pixelByPoint(pointInMaskCrs)
                    if pixel is None:
                        continue
                    value = maskReader.arrayFromPixelOffsetAndSize(pixel.x(), pixel.y(), 1, 1, [1])
                    maskValue = maskReader.maskArray(value, [1], defaultNoDataValue=0)
                    if not maskValue[0][0, 0]:
                        continue

                    # prepare match info
                    pointInRasterCrs = SpatialPoint(poi.crs(), point).toCrs(rasterReader.crs())
                    pixel = rasterReader.pixelByPoint(pointInRasterCrs)
                    attributesDict['match-source'] = rasterReader.source()
                    attributesDict['match-px'] = pixel.x()
                    attributesDict['match-py'] = pixel.y()
                    attributesDict['match-dt'] = targetDate.daysTo(date)

                    if extractProfiles:

                        array = np.array(rasterReader.arrayFromPixelOffsetAndSize(pixel.x(), pixel.y(), 1, 1), float)
                        mask = np.array(rasterReader.maskArray(array))
                        array[~mask] = np.nan
                        y = array.flatten().tolist()

                        if rasterReader.isSpectralRasterLayer(False):
                            x = [rasterReader.wavelength(bandNo) for bandNo in rasterReader.bandNumbers()]
                            attributesDict['match-profile'] = {
                                'y': y,
                                'x': x,
                                'xUnit': 'Nanometers'
                            }
                        else:
                            attributesDict['match-profile'] = {
                                'y': y
                            }

                        data.append(attributesDict)
                        found = True

                    break

                if not found:
                    attributesDict['match-source'] = ''
                    attributesDict['match-px'] = -1
                    attributesDict['match-py'] = -1
                    attributesDict['match-dt'] = -1
                    attributesDict['match-profile'] = {
                        "y": [],
                    }
                    data.append(attributesDict)
                    continue

            # write result
            writer = LibraryDriver().createFromData(data, geometries, 'Match-up results', poi.wkbType(), poi.crs())
            writer.writeToSource(filename)

            result = {self.P_OUTPUT_POINTS: filename}
            self.toc(feedback, result)

        return result
