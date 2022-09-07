from math import ceil
from typing import List, Tuple, Dict, Any

import numpy as np

from enmapboxprocessing.enmapalgorithm import Group, EnMAPProcessingAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import Qgis, QgsProcessingContext, QgsProcessingFeedback
from typeguard import typechecked


@typechecked
class RasterLayerZonalAggregationAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_CATEGORIZED_RASTER, _CATEGORIZED_RASTER = 'categorizedRaster', 'Categorized raster layer'
    P_OUTPUT_TABLE, _OUTPUT_TABLE = 'outputTable', 'Output table'

    def displayName(self) -> str:
        return 'Raster layer zonal aggregation'

    def group(self):
        return Group.Test.value + Group.RasterAnalysis.value

    def shortDescription(self) -> str:
        return 'Aggregates raster layer pixel profiles by categories.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer to be aggregated.'),
            (self._CATEGORIZED_RASTER, 'Categorized raster layer specifying the zones.'),
            (self._OUTPUT_TABLE, self.TableFileDestination)
        ]

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterRasterLayer(self.P_CATEGORIZED_RASTER, self._CATEGORIZED_RASTER)
        self.addParameterVectorDestination(self.P_OUTPUT_TABLE, self._OUTPUT_TABLE)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        zoneRaster = self.parameterAsRasterLayer(parameters, self.P_CATEGORIZED_RASTER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_TABLE, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            categories, classBandNo = Utils.categoriesFromRasterLayer(zoneRaster)

            categorySum = dict()
            categoryN = dict()
            for category in categories:
                for bandNo in range(1, raster.bandCount() + 1):
                    categorySum[(category.value, bandNo)] = 0.
                    categoryN[(category.value, bandNo)] = 0

            rasterReader = RasterReader(raster)
            zoneReader = RasterReader(zoneRaster)
            lineMemoryUsage = rasterReader.lineMemoryUsage(1, Qgis.Float32)
            blockSizeY = min(raster.height(), ceil(Utils.maximumMemoryUsage() / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
                feedback.setProgress(block.yOffset / rasterReader.height() * 100)
                arrayZones = zoneReader.arrayFromBlock(block, [classBandNo])[0]
                for bandNo in range(1, raster.bandCount() + 1):
                    arrayFeatures = rasterReader.arrayFromBlock(block, [bandNo])
                    arrayMask = rasterReader.maskArray(arrayFeatures, [bandNo])[0]
                    features = arrayFeatures[0][arrayMask]
                    zones = arrayZones[arrayMask]
                    for category in categories:
                        zoneIndices = zones == category.value
                        categoryN[(category.value, bandNo)] += np.sum(zoneIndices)
                        categorySum[(category.value, bandNo)] += np.sum(features[zoneIndices])

            # prepare output tabele
            header = ['Zone Name', 'Zone Value'] + [f'Band {bandNo}' for bandNo in range(1, raster.bandCount() + 1)]
            table = [header]
            for category in categories:
                row = [category.name, category.value]
                for bandNo in range(1, raster.bandCount() + 1):
                    row.append(categorySum[(category.value, bandNo)] / categoryN[(category.value, bandNo)])
                table.append(row)

            # we always create a CSV file
            tmpFilename = Utils.tmpFilename(filename, 'result.csv')
            with open(tmpFilename, 'w') as file:
                for row in table:
                    file.write(';'.join(map(str, row)) + '\n')

            # finally translate it into the format selected by the user
            parameters = {"INPUT": tmpFilename, "OUTPUT": filename}
            self.runAlg("native:savefeatures", parameters, None, feedback, context, True)

            result = {self.P_OUTPUT_TABLE: filename}

        return result
