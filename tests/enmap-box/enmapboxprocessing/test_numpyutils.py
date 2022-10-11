from math import nan
from unittest import TestCase

import numpy as np

from enmapboxprocessing.numpyutils import NumpyUtils


class TestNumpyUtils(TestCase):

    def test_nanpercentile1(self):
        a = np.array([1, 2, 3, 4, 5]).reshape((-1, 1, 1))
        self.assertEqual([1, 3, 5], NumpyUtils.nanpercentile(a, q=[0, 50, 100]))

    def test_nanpercentile2(self):
        a = np.array([1, nan, 3, nan, 5]).reshape((-1, 1, 1))
        self.assertEqual([1, 3, 5], NumpyUtils.nanpercentile(a, q=[0, 50, 100]))

    def test_nanpercentile3(self):
        a = np.array([1, nan, nan, 5]).reshape((-1, 1, 1))
        self.assertEqual([1, (1 + 5) / 2, 5], NumpyUtils.nanpercentile(a, q=[0, 50, 100]))

    def test_nanpercentile4(self):
        a = np.array([nan, nan]).reshape((-1, 1, 1))
        self.assertTrue(np.all(np.isnan(NumpyUtils.nanpercentile(a, q=[0, 50, 100]))))

    def test_rebinMean(self):
        a = np.array(list(range(16))).reshape(4, 4)
        self.assertTrue(np.all(np.equal([[2.5, 4.5], [10.5, 12.5]], NumpyUtils.rebinMean(a, (2, 2)))))

    def test_rebinSum(self):
        a = np.array(list(range(16))).reshape(4, 4)
        self.assertTrue(np.all(np.equal([[10, 18], [42, 50]], NumpyUtils.rebinSum(a, (2, 2)))))
