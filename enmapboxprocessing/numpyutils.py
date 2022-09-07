from typing import List, Tuple

import numpy as np

from typeguard import typechecked


@typechecked
class NumpyUtils(object):

    @staticmethod
    def nanpercentile(a: np.ndarray, q: List[float], axis=0) -> List[np.ndarray]:

        if a.ndim != 3:
            raise NotImplementedError()

        if axis != 0:
            raise NotImplementedError()

        def zvalue_from_index(arr, ind):
            nB, nL, nS = arr.shape
            idx = nS * nL * ind + nS * np.arange(nL)[:, None] + np.arange(nS)[None, :]
            return np.take(arr, idx)

        a = np.array(a, dtype=np.float32)

        # valid (non NaN) observations along the first axis
        valid_obs = np.sum(np.isfinite(a), axis=0)
        invalid_pixel = valid_obs == 0

        a[np.isnan(a)] = np.Inf

        # sort - former NaNs will move to the end
        arr = np.sort(a, axis=0)

        result = []
        for qi in q:
            # desired position as well as floor and ceiling of it
            k_arr = (valid_obs - 1) * (qi / 100.0)
            f_arr = np.floor(k_arr).astype(np.int32)
            c_arr = np.ceil(k_arr).astype(np.int32)

            # linear interpolation (like numpy percentile) takes the fractional part of desired position
            floor_value = zvalue_from_index(arr=arr, ind=f_arr)
            floor_weight = (c_arr - k_arr)
            ceil_value = zvalue_from_index(arr=arr, ind=c_arr)
            ceil_weight = (k_arr - f_arr)
            floor_weight[f_arr == c_arr] = 1.  # if floor == ceiling take floor value

            quant_arr = np.array(floor_value * floor_weight + ceil_value * ceil_weight, dtype=np.float32)

            # fill invalid pixels with fill value
            quant_arr[invalid_pixel] = np.NaN

            result.append(quant_arr)

        return result

    @staticmethod
    def rebinMean(a: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
        assert a.ndim == 2
        shape_ = shape[0], a.shape[0] // shape[0], shape[1], a.shape[1] // shape[1]
        return a.reshape(shape_).mean(-1).mean(1)

    @staticmethod
    def rebinSum(a: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
        assert a.ndim == 2
        shape_ = shape[0], a.shape[0] // shape[0], shape[1], a.shape[1] // shape[1]
        return a.reshape(shape_).sum(-1).sum(1)
