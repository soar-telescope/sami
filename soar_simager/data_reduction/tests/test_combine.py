#!/usr/bin/env python 
# -*- coding: utf8 -*-

import unittest
import numpy as np
import os

from ccdproc import Combiner, CCDData

__author__ = 'Bruno Quint'


class TestZeroCombine(unittest.TestCase):

    def test_combine(self):

        ccd1 = CCDData(np.random.normal(size=(10, 10)), unit='adu')
        ccd2 = ccd1.copy()
        ccd3 = ccd1.copy()

        combiner = Combiner([ccd1, ccd2, ccd3])
        combiner.sigma_clipping(low_thresh=2, high_thresh=5)
        combined_data = combiner.median_combine()

        np.testing.assert_equal(combined_data.data, ccd1.data)

    def test_combine_masked(self):

        x = np.random.normal(size=(10, 10))
        x[5,:] = 0
        x = np.ma.masked_where(x == 0, x)

        ccd1 = CCDData(x, unit='adu')
        ccd2 = ccd1.copy()
        ccd3 = ccd1.copy()

        combiner = Combiner([ccd1, ccd2, ccd3])
        combiner.sigma_clipping(low_thresh=2, high_thresh=5)
        combined_data = combiner.median_combine()

        np.testing.assert_equal(combined_data.data, ccd1.data)

if __name__ == '__main__':
    unittest.main()