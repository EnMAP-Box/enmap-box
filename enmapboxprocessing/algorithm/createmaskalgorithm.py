from typing import Optional

from enmapboxprocessing.algorithm.applybandfunctionalgorithmbase import ApplyBandFunctionAlgorithmBase
from enmapboxprocessing.enmapalgorithm import Group
from enmapboxprocessing.typing import QgisDataType
from qgis.core import Qgis
from typeguard import typechecked


@typechecked
class CreateMaskAlgorithm(ApplyBandFunctionAlgorithmBase):

    def displayName(self) -> str:
        return 'Create mask raster layer'

    def group(self):
        return Group.Test.value + Group.Masking.value

    def shortDescription(self) -> str:
        return 'Create a mask raster layer by applying a user-defined evaluation function band-wise to a source raster layer. '

    def helpParameterCode(self) -> str:
        return 'Python code defining the evaluation function. ' \
               'The defined function must return a binary-valued array with same shape as the input array.'

    def code(cls):
        import numpy as np

        def function(array: np.ndarray, noDataValue: float):
            # if source no data value is not defined, use zero as no data value
            if noDataValue is None:
                noDataValue = 0

            # mask no data pixel
            marray = np.not_equal(array, noDataValue)

            # mask inf and nan pixel
            marray[np.logical_not(np.isfinite(array))] = 0

            # include further masking criteria here
            pass

            return marray

        return function

    def outputDataType(self) -> QgisDataType:
        return Qgis.Byte

    def outputNoDataValue(self) -> Optional[float]:
        return None
