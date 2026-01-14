import numpy as np

from enmapboxprocessing.algorithm.applybandfunctionalgorithmbase import ApplyBandFunctionAlgorithmBase
from qgis.core import (Qgis)
from enmapbox.typeguard import typechecked


@typechecked
class SpatialFilterFunctionAlgorithmBase(ApplyBandFunctionAlgorithmBase):

    def outputDataType(self) -> Qgis.DataType:
        return Qgis.Float32

    def outputNoDataValue(self) -> float:
        return float(np.finfo(np.float32).min)

    def prepareInput(self):
        self.array = np.float32(self.array)

    def prepareOutput(self):
        self.outarray[np.logical_not(self.marray)] = self.outputNoDataValue()
