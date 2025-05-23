from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousrasteralgorithm import \
    PrepareRegressionDatasetFromContinuousRasterAlgorithm
from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.typing import RegressorDump, \
    Target
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsProcessingParameterField,
                       QgsProcessingException)
from enmapbox.typeguard import typechecked


@typechecked
class PrepareRegressionDatasetFromContinuousVectorAlgorithm(EnMAPProcessingAlgorithm):
    P_CONTINUOUS_VECTOR, _CONTINUOUS_VECTOR = 'continuousVector', 'Continuous-valued vector layer'
    P_FEATURE_RASTER, _FEATURE_RASTER = 'featureRaster', 'Raster layer with features'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS, = 'excludeBadBands', 'Exclude bad bands'
    P_TARGET_FIELDS, _TARGET_FIELDS = 'targetFields', 'Fields with targets'
    P_OUTPUT_DATASET, _OUTPUT_DATASET = 'outputRegressionDataset', 'Output dataset'

    @classmethod
    def displayName(cls) -> str:
        return 'Create regression dataset (from continuous-valued vector layer and feature raster)'

    def shortDescription(self) -> str:
        return 'Create a regression dataset by sampling data and store the result as a pickle file.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CONTINUOUS_VECTOR,
             'Continuous-valued vector layer specifying sample locations and target data y. '
             'If required, the layer is reprojected and rasterized internally to match the feature raster grid.'),
            (self._FEATURE_RASTER, 'Raster layer used for sampling feature data X.'),
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bands, that are marked as bad bands, '
                                      'or contain no data, inf or nan values in all samples.'),
            (self._TARGET_FIELDS, 'Fields used as target data y. '
                                  'If not selected, the fields defined by the renderer are used. '
                                  'If those are also not specified, an error is raised.'),
            (self._OUTPUT_DATASET, self.PickleFileDestination)
        ]

    def group(self):
        return Group.DatasetCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterVectorLayer(self.P_CONTINUOUS_VECTOR, self._CONTINUOUS_VECTOR)
        self.addParameterRasterLayer(self.P_FEATURE_RASTER, self._FEATURE_RASTER)
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, True, True)
        self.addParameterField(
            self.P_TARGET_FIELDS, self._TARGET_FIELDS, None, self.P_CONTINUOUS_VECTOR,
            QgsProcessingParameterField.DataType.Numeric, True, True, False, True
        )
        self.addParameterFileDestination(self.P_OUTPUT_DATASET, self._OUTPUT_DATASET, self.PickleFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        vector = self.parameterAsVectorLayer(parameters, self.P_CONTINUOUS_VECTOR, context)
        raster = self.parameterAsRasterLayer(parameters, self.P_FEATURE_RASTER, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
        targetFields = self.parameterAsFields(parameters, self.P_TARGET_FIELDS, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATASET, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # derive target fields
            if targetFields is None:
                targets = Utils.targetsFromLayer(vector)
                if targets is None:
                    message = 'Select either a continuous-valued vector layer, or fields with targets.'
                    raise QgsProcessingException(message)
                targetFields = [target.name for target in targets]
            else:
                targets = [Target(field, None) for field in targetFields]

            # rasterize fields
            feedback.pushInfo('Rasterize continuous-valued vector layer')
            alg = RasterizeVectorAlgorithm()
            filenames = list()
            vrtFilename = Utils.tmpFilename(filename, 'regression.vrt')
            noDataValue = Utils.defaultNoDataValue(np.float32)
            for bandNo, targetField in enumerate(targetFields, 1):
                parameters = {
                    alg.P_VECTOR: vector,
                    alg.P_GRID: raster,
                    alg.P_DATA_TYPE: alg.Float32,
                    alg.P_INIT_VALUE: noDataValue,
                    alg.P_BURN_ATTRIBUTE: targetField,
                    alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, f'{bandNo}.tif')
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                filenames.append(parameters[alg.P_OUTPUT_RASTER])
            options = gdal.BuildVRTOptions(separate=True, srcNodata=noDataValue)
            ds = gdal.BuildVRT(vrtFilename, filenames, options=options)
            writer = RasterWriter(ds)
            writer.setNoDataValue(noDataValue)
            writer.close()
            del writer, ds

            # sample data
            feedback.pushInfo('Sample data')
            regression = QgsRasterLayer(vrtFilename)
            X, y, goodBandNumbers, locations = PrepareRegressionDatasetFromContinuousRasterAlgorithm.sampleData(
                raster, regression, excludeBadBands, feedback
            )
            reader = RasterReader(raster)
            features = [reader.bandName(bandNo) for bandNo in goodBandNumbers]
            feedback.pushInfo(f'Sampled data: X=array{list(X.shape)} y=array{list(y.shape)}')

            dump = RegressorDump(
                targets=targets, features=features, X=X, y=y, locations=locations, crs=raster.crs().toWkt()
            )
            dumpDict = dump.__dict__
            Utils.pickleDump(dumpDict, filename)

            result = {self.P_OUTPUT_DATASET: filename}
            self.toc(feedback, result)
        return result
