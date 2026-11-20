from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent, SpatialPoint
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import QDateTime
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)


class MatchRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_TIMESERIES, _TIMESERIES = 'timeSeries', 'Time series'
    P_POI, _POI = 'poi', 'Points of interest'
    P_DATE_FIELD, _DATE_FIELD = 'dateField', 'Date field'
    P_MAXIMUM_TEMPORAL_OFFSET, _MAXIMUM_TEMPORAL_OFFSET = 'maximumTemporalOffset', 'Maximum temporal offset'
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
            (self._MAXIMUM_TEMPORAL_OFFSET,
             'Maximum allowed time difference between the target date and a candidate observation. '
             'The value must be specified as a combination of time units using the format:'
             '<years>y <months>M <days>d <hours>h <minutes>m <seconds>s\n'
             'Examples:'
             '  30d → 30 days\n'
             '  2M 15d → 2 months and 15 days\n'
             '  1y 6M → 1 year and 6 months\n'
             '  2y 3M 5d 4h 30m 15s → 2 years, 3 months, 5 days, 4 hours, 30 minutes, and 15 seconds\n'
             'Units may be omitted if not needed. Use uppercase M for months and lowercase m for minutes.'),
            (self._EXTRACT_PROFILE, 'Whether to extract pixel profiles.'),
            (self._OUTPUT_POINTS, self.VectorFileDestination)
        ]

    def group(self):
        return Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_TIMESERIES, self._TIMESERIES)
        self.addParameterVectorLayer(self.P_POI, self._POI)
        self.addParameterField(self.P_DATE_FIELD, self._DATE_FIELD, None, self.P_POI)
        self.addParameterString(self.P_MAXIMUM_TEMPORAL_OFFSET, self._MAXIMUM_TEMPORAL_OFFSET, None, False, True)
        self.addParameterBoolean(self.P_EXTRACT_PROFILE, self._EXTRACT_PROFILE, False, True)
        self.addParameterVectorDestination(self.P_OUTPUT_POINTS, self._OUTPUT_POINTS)

    @staticmethod
    def temporalOffsetInSec(offset: str) -> float:
        # we assume strings like "2y 3M 5d 4h 30m 15s"
        secs = 0
        for item in offset.split(' '):
            item = item.strip()
            unit = item[-1]
            value = item[:-1]
            if unit == 's':
                secs += int(value)
            elif unit == 'm':
                secs += int(value) * 60
            elif unit == 'h':
                secs += int(value) * 60 * 60
            elif unit == 'd':
                secs += int(value) * 60 * 60 * 24
            elif unit == 'M':
                secs += int(value) * 60 * 60 * 24 * 30.44  # Average month (including leap years)
            elif unit == 'y':
                secs += int(value) * 60 * 60 * 24 * 30.44 * 12  # Average year (including leap years)
            else:
                raise QgsProcessingException('unknown temporal offset unit: ' + unit)

        return secs

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        timeseries = self.parameterAsFile(parameters, self.P_TIMESERIES, context)
        poi = self.parameterAsVectorLayer(parameters, self.P_POI, context)
        dateField = self.parameterAsField(parameters, self.P_DATE_FIELD, context)
        dateFieldIndex = poi.fields().indexFromName(dateField)
        maxTempOffset = self.parameterAsString(parameters, self.P_MAXIMUM_TEMPORAL_OFFSET, context)
        if maxTempOffset is not None:
            maxTempOffsetSec = int(self.temporalOffsetInSec(maxTempOffset))
        extractProfiles = self.parameterAsBoolean(parameters, self.P_EXTRACT_PROFILE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_POINTS, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            pointInfos = list()
            geometries = list()
            dateFirst = QDateTime(9999, 1, 1, 1, 1)
            dateLast = QDateTime(0, 1, 1, 1, 1)

            for feature in poi.getFeatures():
                point = feature.geometry().asPoint()
                attributes = feature.attributes()
                datetime = Utils.parseDateTime(attributes[dateFieldIndex])
                pointInfos.append((point, attributes, datetime))
                geometries.append(feature.geometry())
                dateFirst = min(dateFirst, datetime)
                dateLast = max(dateLast, datetime)

            with open(timeseries, 'r') as file:
                lines = file.readlines()

            rasterInfos = list()
            rasterDates = list()
            for i, line in enumerate(lines):
                raster, mask, date = line.strip().split(',')
                if i == 0:
                    if raster != 'raster' or mask != 'mask' or date != 'date':
                        raise ValueError(
                            f"unexpected field names: raster={raster!r}, "
                            f"mask={mask!r}, date={date!r}"
                        )
                    continue
                if mask == '':
                    mask = raster

                rasterReader = RasterReader(raster)
                maskReader = RasterReader(mask)
                datetime = Utils.parseDateTime(date)
                extent = SpatialExtent.fromLayer(rasterReader.layer).toCrs(poi.crs())

                # filter by dates
                if maxTempOffset is not None:
                    if datetime.addSecs(maxTempOffsetSec) < dateFirst:
                        continue
                    if datetime.addSecs(-1 * maxTempOffsetSec) > dateLast:
                        continue

                # filter by extent
                if not extent.intersects(poi.extent()):
                    continue

                rasterInfos.append((rasterReader, maskReader, datetime, extent))
                rasterDates.append(datetime)

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
                    attributesDict = dict(zip(fieldNames, attributes))
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
