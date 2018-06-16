#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = 'Bruno Quint'

import numpy as np

from astropy.io import fits as pyfits
from astropy import units as u
from ccdproc import CCDData, combine

from soar_sami.io.logging import get_logger


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
        Combine.__init__(self, verbose=verbose, debug=debug)
        self.input_list = input_list
        self.output_filename = output_file

    def run(self):
        list_of_data = []
        for f in self.input_list:
            hdr = pyfits.getheader(f)
            data = pyfits.getdata(f)
            data = CCDData(data, unit=u.adu)
            list_of_data.append(data)

        # Parameter obtained from PySOAR, written by Luciano Fraga
        master_bias = combine(list_of_data, method='average', mem_limit=6.4e7,
                              minmax_clip=True)

        master_bias.header = hdr
        if self.output_filename is None:
            master_bias.write('0ZERO.fits')

        else:
            master_bias.write(self.output_filename)


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

        list_of_data = []
        for f in self.input_list:

            self.debug('Processing file: {:s}'.format(f))
            hdr = pyfits.getheader(f)
            data = pyfits.getdata(f)

            x_center = data.shape[1] // 2
            x_bsize = int(0.05 * data.shape[1])
            x1, x2 = x_center - x_bsize, x_center + x_bsize
            x_where = np.zeros_like(data)
            x_where[:, x1:x2] = 1

            y_center = data.shape[0] // 2
            y_bsize = int(0.05 * data.shape[0])
            y1, y2 = y_center - y_bsize, y_center + y_bsize
            y_where = np.zeros_like(data)
            y_where[y1:y2, :] = 1

            where = np.where(x_where * y_where == 1, True, False)
            norm_factor = np.median(data[where])
            data /= norm_factor

            data = CCDData(data, unit=u.adu)
            list_of_data.append(data)

        # Parameter obtained from PySOAR, written by Luciano Fraga
        master_flat = combine(list_of_data, method='median', mem_limit=6.4e7,
                              sigma_clip=True)

        master_flat.header = hdr
        if self.output_filename is None:

            filter_name = hdr['FILTERS'].strip()
            binning = int(hdr['CCDSUM'].strip().split(' ')[0])
            self.debug('Binning: {:d}'.format(binning))

            filename = '1NSFLAT{0:d}x{0:d}_{1:s}.fits'.format(
                binning, filter_name)

            master_flat.write(filename, overwrite=True)

        else:
            master_flat.write(self.output_filename, overwrite=True)
