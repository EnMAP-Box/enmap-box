from math import nan
from typing import List, Tuple

import numpy as np

from typeguard import typechecked


@typechecked
def rbfEnsemblePrediction(
        X: np.ndarray, Y: np.ndarray, X2: np.ndarray, rbfFwhms: List[float], rbfUserWeights: List[float] = None,
        rbfCutOffValue=0.01
) -> np.ndarray:
    assert X.ndim == 1  # X[ndates]
    assert X2.ndim == 1  # X[ndates2]
    assert Y.ndim == 2  # Y[nsamples, ndates]
    assert X.shape[0] == Y.shape[1]
    if rbfUserWeights is None:
        rbfUserWeights = [1.] * len(rbfFwhms)
    assert len(rbfFwhms) == len(rbfUserWeights)

    Y2 = list()  # predicted values
    D = list()  # data availability scores

    for rbfFwhm, rbfUserWeight in zip(rbfFwhms, rbfUserWeights):
        Y2i, Di = rbfPrediction(X, Y, X2, rbfFwhm, rbfUserWeight, rbfCutOffValue)
        Y2.append(Y2i)
        D.append(Di)

    Y2 = np.nansum(np.multiply(Y2, D), axis=0) / np.sum(D, axis=0)
    return Y2


@typechecked
def rbfPrediction(
        X: np.ndarray, Y: np.ndarray, X2: np.ndarray, rbfFwhm: float, rbfUserWeight: float, rbfCutOffValue: float
) -> Tuple[np.ndarray, np.ndarray]:
    assert X.ndim == 1  # X[ndates]
    assert X2.ndim == 1  # X[ndates2]
    assert Y.ndim == 2  # Y[nsamples, ndates]
    assert X.shape[0] == Y.shape[1]

    M = np.isfinite(Y)  # data availability mask
    Y2 = list()  # predicted values
    D = list()  # data availability scores

    for targetDecimalYear in X2:
        weights = rbfWeights(X, float(targetDecimalYear), rbfFwhm)
        weightsSum = weights.sum()
        valid = np.greater_equal(weights, rbfCutOffValue)
        Wi = weights[valid].reshape((1, -1))
        Yi = Y[:, valid]
        Mi = M[:, valid]

        YiSum = np.nansum(Yi * Wi, axis=1)  # weighted sum of values; nan values are skipped
        MiSum = np.sum(Mi * Wi, axis=1)  # sum of weights; note that weights corresponding to nan values are zeroed out

        if weightsSum != 0:
            YiMean = YiSum / MiSum  # predicted value
            Di = MiSum / weights.sum() * rbfUserWeight
        else:
            YiMean = np.full_like(MiSum, nan)
            Di = np.zeros_like(MiSum)

        Y2.append(YiMean)
        D.append(Di)

    Y2 = np.array(Y2).T
    D = np.array(D).T

    assert Y2.shape[1] == X2.shape[0]
    assert Y2.shape == D.shape

    return Y2, D


@typechecked
def rbfWeights(decimalYears: np.ndarray, rbfCenter: float, rbfFwhm: float):
    """Returns RBF kernel weights (values between 0 and 1) for given decimalYears."""

    sigma = rbfFwhm / 2.355
    return np.exp(-(decimalYears - rbfCenter) ** 2 / (2 * sigma ** 2))
