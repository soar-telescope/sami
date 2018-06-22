#!/usr/bin/env python 

from __future__ import division, print_function

import numpy
import unittest

from soar_sami.tools import slices

__author__ = 'Bruno Quint'


class TestSlices(unittest.TestCase):

    def test_iraf2python(self):

        x_left = 1
        x_right = 10
        y_left = 2
        y_right = 20

        test_string = "[{:d}:{:d},{:d}:{:d}]".format(
            x_left, x_right, y_left, y_right)

        x, y = slices.iraf2python(test_string)

        self.assertIsInstance(x, numpy.ndarray)
        self.assertIsInstance(y, numpy.ndarray)

        self.assertEqual(x_left, x[0] + 1)
        self.assertEqual(x_right, x[1])

        self.assertEqual(y_left, y[0] + 1)
        self.assertEqual(y_right, y[1])

    def test_python2iraf(self):

        x_left = 1
        x_right = 10
        y_left = 2
        y_right = 20

        s = slices.python2iraf(x_left, x_right, y_left, y_right)
        x, y = slices.iraf2python(s)

        self.assertEqual(x[0], x_left)
        self.assertEqual(x[1], x_right)

        self.assertEqual(y[0], y_left)
        self.assertEqual(y[1], y_right)


if __name__ == '__main__':
    unittest.main()