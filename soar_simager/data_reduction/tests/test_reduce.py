#!/usr/bin/env python 
# -*- coding: utf8 -*-

import unittest
import numpy as _np

from astropy import wcs
from soar_simager.data_reduction import reduce
from soar_simager.io import pyfits

__author__ = 'Bruno Quint'


class TestReducer(unittest.TestCase):

    def setUp(self):

        self.reducer = reduce.Reducer()

    def test_if_can_clean_one_line(self):

        data = _np.zeros((10,10))
        data[5] = 1.
        data = self.reducer.clean_line(data, 0, 10, 5, 2)

        _np.testing.assert_equal(data, _np.zeros_like(data))

    def test_if_can_clean_one_column(self):

        data = _np.zeros((10, 10))
        data[:, 5] = 1.
        data = self.reducer.clean_column(data, 5, 0, 10, 2)

        _np.testing.assert_equal(data, _np.zeros_like(data))

    def test_merge(self):

        hdul = pyfits.HDUList()
        hdul.append(pyfits.PrimaryHDU())

        for i in range(1, 5):

            ihdu = pyfits.ImageHDU()
            ihdu.data = _np.ones((15,15))
            ihdu.data[:,:5]

            ihdu.header['DETSIZE'] = "[1:30,1:30]"
            ihdu.header['CCDSUM'] = "1 1"
            ihdu.header['TRIMSEC'] = "[1:15,1:15]"

            ihdu.header['DETSEC'] = "[{:d}:{:d},{:d}:{:d}]".format(
                1 + 15 * ((i - 1) // 2),
                15 + 15 * ((i - 1) // 2),
                1 + 15 * ((i - 1) % 2),
                15 + 15 * ((i - 1) % 2),
            )

            ihdu.header['BIASSEC'] = "[1:5,1:15]"

            hdul.append(ihdu)

        data, header, prefix = self.reducer.merge(hdul)

        self.assertEqual(prefix, 'm_')
        self.assertIsInstance(data, _np.ndarray)
        self.assertIsInstance(header, pyfits.Header)


class TestWCS(unittest.TestCase):

    def setUp(self):

        self.reducer = reduce.Reducer()

    def test_create_wcs(self):

        d = _np.ones((2000, 2000))
        h = pyfits.Header()

        h['PIXSCAL1'] = 0.045
        h['PIXSCAL2'] = 0.045
        h['CCDSUM'] = '2 2'
        h['RA'] = "00:00:00"
        h['DEC'] = "00:00:00"
        h['DECPANGL'] = 0

        h = self.reducer.create_wcs(d, h)

        w = wcs.WCS(header=h)

        pixcrd = _np.array([[0, 0], [24, 38], [45, 98]], _np.float_)

        world = w.wcs_pix2world(pixcrd, 1)

        pixcrd2 = w.wcs_world2pix(world, 1)

        _np.testing.assert_almost_equal(pixcrd, pixcrd2)

if __name__ == '__main__':
    unittest.main()