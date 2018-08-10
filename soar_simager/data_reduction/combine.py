#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = 'Bruno Quint'

import ccdproc
import numpy as np

from astropy.io import fits as pyfits

from soar_simager.io.logging import get_logger


def scale_flat_sami(data):
    """
    Args:
        data (numpy.ndarray) : data used to evaluate the scaling function.

    Returns:
        scale_factor (float) : the inverse of the median of central reagion of
        the masked data.

    """
    data = np.ma.masked_invalid(data)
    h, w = data.shape

    r1, r2 = h // 2 - h // 10, h // 2 + h // 10
    c1, c2 = w // 2 - w // 10, w // 2 + w // 10

    data = data[r1:r2, c1:c2]
    scale_factor = 1. / np.ma.median(data)

    return scale_factor


class Combine:

    def __init__(self, verbose=False, debug=False):

        self._log = get_logger(__name__)
        self.set_verbose(verbose)
        self.set_debug(debug)
        return

    def debug(self, message):
        """Print a debug message using the logging system."""
        self._log.debug(message)

    def info(self, message):
        """Print an info message using the logging system."""
        self._log.info(message)

    def set_debug(self, debug):
        """
        Turn on debug mode.

        Parameter
        ---------
            debug : bool
        """
        if debug:
            self._log.setLevel("DEBUG")

    def set_verbose(self, verbose):
        """
        Turn on verbose mode.

        Parameter
        ---------
            verbose : bool
        """
        if verbose:
            self._log.setLevel("INFO")
        else:
            self._log.setLevel("WARNING")

    def warn(self, message):
        """Print a warning message using the logging system."""
        self._log.warning(message)


class ZeroCombine(Combine):

    def __init__(self, input_list, output_file=None, verbose=False, debug=False):
        """
        Class created to help combining zero files.

        Args:

            input_list (list) : A list containing the input files.

            output_file (str) : The output filename (optional).

            verbose (bool) : Turn on verbose mode? (default = False)

            debug (bool) : Turn on debug mode? (default = False)

        """
        Combine.__init__(self, verbose=verbose, debug=debug)
        self.input_list = input_list
        self.output_filename = output_file

    def run(self):

        header = pyfits.getheader(self.input_list[0])
        bx, by = header['CCDSUM'].strip().split()

        # Parameter obtained from PySOAR, written by Luciano Fraga
        master_bias = ccdproc.combine(
            self.input_list, method='average', mem_limit=6.4e7,
            minmax_clip=True, unit='adu')

        if self.output_filename is None:
            self.output_filename = "0Zero{}x{}".format(bx, by)

        pyfits.writeto(
            self.output_filename, master_bias.data, header)


class FlatCombine(Combine):

    def __init__(self, input_list, output_file=None, verbose=False,
                 debug=False):
        """
        Class created to help combining flats. By now, it does not do any type
        or organization. It will simply combine all the flat images that are
        given as argument.

        Args:

            input_list (list) : A list containing the input files.

            output_file (str) : The output filename (optional).

            verbose (bool) : Turn on verbose mode? (default = False)

            debug (bool) : Turn on debug mode? (default = False)

        """

        Combine.__init__(self, verbose=verbose, debug=debug)
        self.input_list = input_list
        self.output_filename = output_file

    def run(self):

        header = pyfits.getheader(self.input_list[0])

        if header['INSTRUME'] == 'SAM':
            scale_function = scale_flat_sami

        # TODO - Scale Function for SOI and SIFS

        # Parameter obtained from PySOAR, written by Luciano Fraga
        ccd_data = ccdproc.combine(
            self.input_list, method='median', mem_limit=6.4e7, sigma_clip=True,
            unit='adu', scale=scale_function
        )

        data = ccd_data.data

        if self.output_filename is None:

            filter_name = header['FILTERS'].strip()
            binning = int(header['CCDSUM'].strip().split(' ')[0])
            self.debug('Binning: {:d}'.format(binning))

            self.output_filename = \
                '1NSFLAT{0:d}x{0:d}_{1:s}.fits'.format(
                    binning, filter_name)

        pyfits.writeto(self.output_filename, data, header)
