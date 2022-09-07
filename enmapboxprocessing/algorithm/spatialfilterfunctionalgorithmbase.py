import numpy as np

from enmapboxprocessing.algorithm.applybandfunctionalgorithmbase import ApplyBandFunctionAlgorithmBase
from enmapboxprocessing.typing import QgisDataType
from qgis.core import (Qgis)
from typeguard import typechecked


@typechecked
class SpatialFilterFunctionAlgorithmBase(ApplyBandFunctionAlgorithmBase):

    def outputDataType(self) -> QgisDataType:
        return Qgis.Float32

    def outputNoDataValue(self) -> float:
        return float(np.finfo(np.float32).min)

    def prepareInput(self):
        self.array = np.float32(self.array)

    def prepareOutput(self):
        self.outarray[np.logical_not(self.marray)] = self.outputNoDataValue()
