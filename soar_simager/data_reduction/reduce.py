#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    SAMI XJoin

    This script simply joins the four existing extensions inside a FITS file
    created during observations with SAMI (SAM Imager). During the reduce,
    it also fits a 2nd degree polynomium to the OVERSCAN region that is
    subtracted from the corresponding image.

    The user also may want to add flags in order to reduce the images
    according to the following options (in order):

    - BIAS subtraction;
    - DARK subtraction;
    - Remove hot pixels and cosmic rays;
    - Remove overglow using a long exposure DARK image;
    - Divide by the FLAT;
    - Divide by the exposure time;

    The documentation for each reduce is shown in the corresponding function.

    Todo
    ----
    - Use multithread or multiprocessing to run this script faster.
    - Use astropy.ccdproc to reduce the data.

    Bruno Quint (bquint at ctio.noao.edu)
    May 2016

    Thanks to Andrei Tokovinin and Claudia M. de Oliveira for the ideas that
    were implemented here.
"""

import numpy as _np

from ccdproc import cosmicray_lacosmic as _cosmicray_lacosmic
from scipy import stats

from astropy import wcs
from astropy.coordinates import SkyCoord
from astropy import units as u

from soar_simager.io import pyfits as _pyfits
from soar_simager.io.logging import get_logger
from soar_simager.tools import slices

logger = get_logger(__name__)


# Piece of code from cosmics.py
# We define the laplacian kernel to be used
_laplkernel = _np.array([[0.0, -1.0, 0.0], [-1.0, 4.0, -1.0], [0.0, -1.0, 0.0]])

# Other kernels :
_growkernel = _np.ones((3, 3))

# dilation structure for some morphological operations
_dilstruct = _np.ones((5, 5))
_dilstruct[0, 0] = 0
_dilstruct[0, 4] = 0
_dilstruct[4, 0] = 0
_dilstruct[4, 4] = 0


class Reducer:
    """
    This class holds all the methods used to join the extensions within a
    FITS file obtained with SAMI.

    Parameters
    ----------
        zero_file : str
            The filename of the master zero that will be used in subtraction.

        clean : bool
            Clean bad collumns by taking the _median value of the pixels around
            them.

        cosmic_rays : bool
            Clean cosmic rays using LACosmic package. See noted bellow for
            reference.

        dark_file : str
            Master Dark's filename to be used for dark subtraction.

        debug : bool
            Turn on debug mode with lots of printing.

        flat_file : str
            Master Flat filename to be used for normalization.

        glow_file : str
            Master file that contains the lateral glowings sometimes present in
            SAMI's data.

        time : bool
            Divide each pixel's values by the exposure time and update header.

        verbose : bool
            Turn on verbose mode (not so talktive as debug mode).

    See also
    --------
        LACosmic - http://www.astro.yale.edu/dokkum/lacosmic/
    """

    gain = [2.6, 2.6, 2.6, 2.6]
    read_noise = [10., 10., 10., 10.]

    def __init__(self, clean=False, cosmic_rays=False, dark_file=None,
                 debug=False, flat_file=None, glow_file=None, merge=False,
                 overscan=False, norm_flat=False, time=False, verbose=False,
                 zero_file=None):

        logger.setLevel("ERROR")

        if verbose:
            logger.setLevel("INFO")

        if debug:
            logger.setLevel("DEBUG")

        self.clean = clean
        self.cosmic_rays = cosmic_rays
        self.dark_file = dark_file
        self.flat_file = flat_file
        self.glow_file = glow_file
        self._merge = merge
        self.norm_flat = norm_flat
        self.overscan = overscan
        self.time = time
        self.zero_file = zero_file

        return

    def reduce(self, hdu_list, prefix=""):

        # If the number of extensions is just 1, then the file is already
        # processed.
        if len(hdu_list) == 1:
            return hdu_list, ''

        # Merge file
        data, header, prefix = self.merge(hdu_list)

        # Correct ZERO
        data, header, prefix = self.correct_zero(
            data, header, prefix, self.zero_file
        )

        # Correct DARK
        data, header, prefix = self.correct_dark(
            data, header, prefix, self.dark_file
        )

        # Remove cosmic rays and hot pixels
        data, header, prefix = self.remove_cosmic_rays(
            data, header, prefix, self.cosmic_rays
        )

        # Remove lateral glows
        data, header, prefix = self.correct_lateral_glow(
            data, header, prefix, self.glow_file
        )

        # Correct FLAT
        data, header, prefix = self.correct_flat(
            data, header, prefix, self.flat_file
        )

        # Normalize by the EXPOSURE TIME
        data, header, prefix = self.divide_by_exposuretime(
            data, header, prefix, self.time
        )

        # Clean known bad columns and lines
        data, header, prefix = self.clean_hot_columns_and_lines(
            data, header, prefix, self.clean
        )

        # Add WCS
        data, header = self.create_wcs(
            data, header
        )

        return data, header, prefix

    @staticmethod
    def create_wcs(data, header):
        """
        Creates a first guess of the WCS using the telescope coordinates, the
        CCDSUM (binning), position angle and plate scale.

        Parameters
        ----------
            data : numpy.ndarray
                2D array with the data.

            header : astropy.io.fits.Header
                Primary Header to be updated.

        Returns
        -------
            header : astropy.io.fits.Header
                Primary Header with updated WCS information.
        """
        h = header

        if 'EQUINOX' not in h:
            h['EQUINOX'] = 2000.

        if 'EPOCH' not in h:
            h['EPOCH'] = 2000.

        if h['PIXSCAL1'] != h['PIXSCAL2']:
            logger.warning('Pixel scales for X and Y do not mach.')

        if h['OBSTYPE'] != 'OBJECT':
            return data, header

        binning = _np.array([int(b) for b in h['CCDSUM'].split(' ')])
        plate_scale = h['PIXSCAL1'] * u.arcsec
        p = plate_scale.to('degree').value
        w = wcs.WCS(naxis=2)

        try:
            coordinates = SkyCoord(ra=h['RA'], dec=h['DEC'],
                                   unit=(u.hourangle, u.deg))

        except ValueError:

            logger.error(
                '"RA" and "DEC" missing. Using "TELRA" and "TELDEC" instead.')

            coordinates = SkyCoord(ra=h['TELRA'], dec=h['TELDEC'],
                                   unit=(u.hourangle, u.deg))

        ra = coordinates.ra.to('degree').value
        dec = coordinates.dec.to('degree').value

        w.wcs.crpix = [data.shape[1] / 2, data.shape[0] / 2]
        w.wcs.cdelt = p * binning
        w.wcs.crval = [ra, dec]
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        wcs_header = w.to_header()

        theta = _np.deg2rad(h['DECPANGL'])
        wcs_header['cd1_1'] = p * binning[0] * _np.cos(theta)
        wcs_header['cd2_2'] = p * binning[0] * _np.cos(theta)
        wcs_header['cd1_2'] = p * binning[0] * _np.sin(theta)
        wcs_header['cd2_1'] = - p * binning[0] * _np.sin(theta)

        for key in wcs_header.keys():
            header[key] = wcs_header[key]

        return data, header

    @staticmethod
    def check_header(hdu_list, prefix):

        for i in range(5):

            h = hdu_list[i].header

            try:
                h['RADESYSa'] = h['RADECSYS']
                del h['RADECSYS']
            except KeyError:
                pass

            if 'EQUINOX' in h and 'unavail' in h['EQUINOX']:
                h['EQUINOX'] = 2000.

            if 'EPOCH' not in h:
                h['EPOCH'] = 2000.

        return hdu_list, prefix

    @staticmethod
    def clean_column(_data, x0, y0, yf, n=5):
        """
        Substitutes a single column by the _median of the neighbours columns.

        Args:

            _data (numpy.ndarray) : A 2D numpy array that contains the data.

            x0 (int) : X position of the pixel to be cleaned.

            y0 (int) : Start position of the column.

            yf (int) : Final position of the column.

            n (int, optional) : Number of neighbour columns (Default=5).

        Returns:

            _data (numpy.ndarray) : Processed 2D numpy array.

        See also:

            Reducer.clean_columns
            Reducer.clean_line
            Reducer.clean_lines
        """

        if not isinstance(_data, _np.ndarray):
            raise (TypeError, 'Please, use a np.array as input')

        if _data.ndim is not 2:
            raise (TypeError, 'Data contains %d dimensions while it was '
                              'expected 2 dimensions.')

        t1 = _data[y0:yf, x0 - n:x0]
        t2 = _data[y0:yf, x0 + 1:x0 + n]
        t = _np.hstack((t1, t2))
        _data[y0:yf, x0] = _np.median(t, axis=1)

        return _data

    def clean_columns(self, data, header):
        """
        Clean the known bad columns that exists in most of SAMI's, SOI's or
        SIFS's data. This method is meant to be overwritten via inheritance.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

        See also:

            Reducer.clean_column
            Reducer.clean_line
            Reducer.clean_lines
        """
        return data, header

    @staticmethod
    def clean_line(_data, x0, xf, y, n=5):
        """
        Substitutes a single column by the _median of the neighbours columns.

        Args:

            _data (numpy.ndarray) : A 2D numpy array that contains the data.

            x0 (int) : Start position of the line.

            xf (int) : Final position of the line.

            y (int) : Y position of the pixel to be cleaned.

            n (int) : Number of neighbour columns. (Default=5)

        See also:

            Reducer.clean_column
            Reducer.clean_columns
            Reducer.clean_lines
        """
        if not isinstance(_data, _np.ndarray):
            raise (TypeError, 'Please, use a np.array as input')

        if _data.ndim is not 2:
            raise (TypeError, 'Data contains %d dimensions while it was '
                              'expected 2 dimensions.')

        t1 = _data[y - n:y, x0:xf]
        t2 = _data[y + 1:y + n, x0:xf]
        t = _np.vstack((t1, t2))
        _data[y, x0:xf] = _np.median(t, axis=0)

        return _data

    def clean_lines(self, data, header):
        """
        Clean the known bad lines that exists in most of SAMI's, SOI's or
        SIFS's data. This method is meant to be overwritten via inheritance.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

        See also:

            Reducer.clean_column
            Reducer.clean_line
            Reducer.clean_lines
        """
        return data, header

    def clean_hot_columns_and_lines(self, data, header, prefix, clean):
        """
        Clean known hot columns and lines from SAMI's images.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

            prefix (str) : File prefix that is added after each reduce.

            clean (bool) : Should I perform the clean?

        See also:

            Reducer.clean_column
            Reducer.clean_columns
            Reducer.clean_line
            Reducer.clean_lines
        """
        if clean is True:

            data = self.clean_columns(data, header)
            data = self.clean_lines(data, header)
            header.add_history('Cleaned bad columns and lines.')
            prefix = 'c' + prefix

        return data, header, prefix

    @staticmethod
    def correct_dark(data, header, prefix, dark_file=None):
        """
        Subtract the dark file from data and add HISTORY to header.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

            prefix : str
                File prefix that is added after each reduce.

            dark_file: str | None
                Master Dark filename. If None is given, nothing is done.
        """

        if not isinstance(prefix, str):
            raise (TypeError, 'Expected string but found %s instead.' %
                   prefix.__class__)

        if dark_file is not None:

            dark = _pyfits.open(dark_file)[0]
            dark.data = dark.data / float(dark.header['EXPTIME'])

            data = data - dark.data * header['EXPTIME']
            header['DARKFILE'] = dark_file
            prefix = 'd' + prefix

        return data, header, prefix

    @staticmethod
    def correct_flat(data, header, prefix, flat_file):
        """
        Divide the image by the master flat file and add HISTORY to header.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

            prefix (str) : File prefix that is added after each reduce.

            flat_file (str or None) : Master flat filename. If None is given,
            nothing is done.
        """
        if not isinstance(prefix, str):
            raise (TypeError, 'Expected string but found %s instead.' %
                   prefix.__class__)

        if flat_file is not None:
            flat = _pyfits.open(flat_file)[0]

            data /= flat.data
            header['FLATFILE'] = flat_file
            prefix = 'f' + prefix

        return data, header, prefix

    def correct_lateral_glow(self, data, header, prefix, glow_file):
        """
        Remove lateral glows by scaling the glows in the `glow_file` based
         on `data` and subtracting it.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

            prefix : str
                Filename prefix to flag images that were clean.

            glow_file : str
                Path to a long dark file that contains the lateral glow.
        """

        if glow_file is not None:

            # Create four different regions.
            regions = [
                [_np.median(data[539:589, 6:56]),  # Top Left
                 _np.median(data[539:589, 975:1019])],  # Top Right
                [_np.median(data[449:506, 6:56]),  # Bottom Left
                 _np.median(data[449:506, 975:1019])]  # Bottom Right
            ]

            min_std_region = _np.argmin(regions) % 2

            # The upper reg has background lower or equal to the lower reg
            midpt1 = regions[0][min_std_region]
            midpt2 = regions[1][min_std_region]
            diff = midpt2 - midpt1

            dark = _pyfits.getdata(glow_file)
            dark = self.clean_columns(dark)
            dark = self.clean_lines(dark)

            dark_regions = [
                [_np.median(dark[539:589, 6:56]),  # Top Left
                 _np.median(dark[539:589, 975:1019])],  # Top Right
                [_np.median(dark[449:506, 6:56]),  # Bottom Left
                 _np.median(dark[449:506, 975:1019])]  # Bottom Right
            ]

            dark_midpt1 = dark_regions[0][min_std_region]
            dark_midpt2 = dark_regions[1][min_std_region]

            dark_diff = dark_midpt2 - dark_midpt1
            dark -= dark_midpt1

            k = diff / dark_diff
            temp_dark = dark * k
            data -= midpt1
            data -= temp_dark

            header.add_history('Lateral glow removed using %s file' % glow_file)
            prefix = 'g' + prefix

        return data, header, prefix

    @staticmethod
    def correct_zero(data, header, prefix, zero_file):
        """
        Subtract zero from data.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

            prefix (str) : File prefix that is added after each reduce.

            zero_file (str | None) : Master Bias filename. If None is given,
            nothing is done.

        """
        from os.path import abspath

        if zero_file is not None:

            zero = _pyfits.open(abspath(zero_file))[0]
            data = data - zero.data
            header['BIASFILE'] = zero_file
            prefix = 'z' + prefix

        return data, header, prefix

    @staticmethod
    def divide_by_exposuretime(data, header, prefix, time):
        """
            Divide the image by the exposure time and add HISTORY to header.

            Args:

                data (numpy.ndarray) : A 2D numpy array that contains the data.

                header (astropy.io.fits.Header) : A header that will be updated.

                prefix : str
                    File prefix that is added after each reduce.

                time: bool
                    Divide image by exposure time?
        """
        if time is True:

            h = header

            try:

                h['UNITS'] = 'adu / s'
                t = float(h['EXPTIME'])
                d = data / t

                header = h
                data = d

            except AttributeError:
                header = h

            except KeyError:
                pass

            prefix = 't' + prefix

        return data, header, prefix

    def get_header(self, hdu_source):
        """
        Return the header of the primary HDU extension of a FITS file.

        Args:

            hdu_source (str or astropy.io.fits.HDUList) : HDUList or name of the
            file which contains a HDUList.
        """
        from os.path import exists

        if isinstance(hdu_source, str):

            if not exists(hdu_source):
                raise (IOError, '%s file not found.' % hdu_source)

            hdu_source = _pyfits.open(hdu_source)

        h0 = hdu_source[0].header
        h1 = hdu_source[1].header

        h0.append('UNITS')
        h0.set('UNITS', value='ADU', comment='Pixel intensity units.')

        # Save the CCD binning in the main header
        h0['CCDSUM'] = h1['CCDSUM']
        h0['DETSEC'] = h1['DETSEC']

        # Save the area that corresponds to each amplifier
        bin_size = _np.array(h0['CCDSUM'].split(' '), dtype=int)

        dx, dy = slices.iraf2python(h0['DETSEC'])
        dx, dy = dx // bin_size[0], dy // bin_size[1]

        h0['AMP_SEC1'] = slices.python2iraf(
            dx[0], dx[1], dy[0], dy[1])

        h0['AMP_SEC2'] = slices.python2iraf(
            dx[0] + dx[1], dx[1] + dx[1], dy[0], dy[1])

        h0['AMP_SEC3'] = slices.python2iraf(
            dx[0], dx[1], dy[0] + dy[1], dy[1] + dy[1])

        h0['AMP_SEC4'] = slices.python2iraf(
            dx[0] + dx[1], dx[1] + dx[1], dy[0] + dy[1], dy[1] + dy[1])

        return h0

    def get_prefix(self):
        """
        Return a prefix to be added to the file deppending on the data
        reduction steps.

        Returns
        -------
            prefix : (str)
                The prefix that can be used.
                    m = merged amplifiers.
                    z = zero subtracted.
                    f = flat corrected.
        """

        prefix = 'm_'

        if self.zero_file:
            prefix = 'z' + prefix

        if self.dark_file:
            prefix = 'd' + prefix

        if self.flat_file:
            prefix = 'f' + prefix

        return prefix

    def merge(self,  hdul):
        """
        Open a FITS image and try to join its extensions in a single array.

        Args:

            hdul (astropy.io.fits.HDUList) : an HDUList that contains one
            PrimaryHDU and four ImageHDU

        """
        w, h = slices.iraf2python(hdul[1].header['DETSIZE'])

        if len(hdul) is 1:
            logger.warning('%s file contains a single extension. ' % hdul +
                           'Not doing anything')
            return hdul[0].data

        # Correct for binning
        bin_size = _np.array(hdul[1].header['CCDSUM'].split(' '),
                             dtype=int)
        bw, bh = w[1] // bin_size[0], h[1] // bin_size[1]

        # Create empty full frame
        new_data = _np.empty((bh, bw), dtype=float)

        # Process each extension
        for i in range(1, 5):
            tx, ty = slices.iraf2python(hdul[i].header['TRIMSEC'])
            bx, by = slices.iraf2python(hdul[i].header['BIASSEC'])

            data = hdul[i].data
            trim = data[ty[0]:ty[1], tx[0]:tx[1]]
            bias = data[by[0]:by[1], bx[0]:bx[1]]

            # Collapse the bias columns to a single column.
            bias = _np.median(bias, axis=1)

            # Fit and remove OVERSCAN
            x = _np.arange(bias.size) + 1
            bias_fit_pars = _np.polyfit(x, bias, 2)  # Last par = inf
            bias_fit = _np.polyval(bias_fit_pars, x)
            bias_fit = bias_fit.reshape((bias_fit.size, 1))
            bias_fit = _np.repeat(bias_fit, trim.shape[1], axis=1)

            trim = trim - bias_fit
            dx, dy = slices.iraf2python(hdul[i].header['DETSEC'])
            dx, dy = dx // bin_size[0], dy // bin_size[1]
            new_data[dy[0]:dy[1], dx[0]:dx[1]] = trim

        header = self.get_header(hdul)

        return new_data, header, "m_"

    @staticmethod
    def remove_cosmic_rays(data, header, prefix, cosmic_rays):
        """
        Use LACosmic to remove cosmic rays.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

            prefix : str
                Filename prefix to flag images that were clean.

            cosmic_rays : bool
                Flag to indicate if cosmic rays removal should be performed.
        """
        if cosmic_rays:

            d = data
            d, _ = _cosmicray_lacosmic(
                d, gain=2.6, readnoise=10.0, sigclip=2.5, sigfrac=0.3,
                objlim=5.0)
            d /= 2.6

            h = header
            h.add_history(
                'Cosmic rays and hot pixels removed using LACosmic')

            data = d
            header = h

        return data, header, prefix

    @staticmethod
    def remove_wcs(header):

        return header


class SamiReducer(Reducer):

    def reduce(self, hdu_list, prefix=""):

        # If the number of extensions is just 1, then the file is already
        # processed.
        if len(hdu_list) == 1:
            return hdu_list, ''

        # Merge file
        data, header, prefix = self.merge(hdu_list)

        # Removing bad column and line
        data, header, prefix = self.remove_central_bad_columns(
            data, header, prefix,
        )

        # Correct ZERO
        data, header, prefix = self.correct_zero(
            data, header, prefix, self.zero_file
        )

        # Correct DARK
        data, header, prefix = self.correct_dark(
            data, header, prefix, self.dark_file
        )

        # Remove cosmic rays and hot pixels
        data, header, prefix = self.remove_cosmic_rays(
            data, header, prefix, self.cosmic_rays
        )

        # Remove lateral glows
        data, header, prefix = self.correct_lateral_glow(
            data, header, prefix, self.glow_file
        )

        # Correct FLAT
        data, header, prefix = self.correct_flat(
            data, header, prefix, self.flat_file
        )

        # Normalize by the EXPOSURE TIME
        data, header, prefix = self.divide_by_exposuretime(
            data, header, prefix, self.time
        )

        # Clean known bad columns and lines
        data, header, prefix = self.clean_hot_columns_and_lines(
            data, header, prefix, self.clean
        )

        # Add WCS
        data, header = self.create_wcs(
            data, header
        )

        return data, header, prefix

    def clean_columns(self, data, header):
        """
        Clean the known bad columns that exists in most of SAMI's, SOI's or
        SIFS's data. This method is meant to be overwritten via inheritance.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

        See also:

            Reducer.clean_column
            Reducer.clean_line
            Reducer.clean_lines
        """
        binning = header['CCDSUM'].split(' ')[0]
        binning = int(binning.strip())

        if binning == 4:
            bad_columns = [
                [167, 0, 513],
                [213, 513, 1023],
                [304, 0, 513],
                [309, 1, 512],
                [386, 0, 513],
                [476, 0, 513],
                [602, 0, 513],
                [671, 0, 513],
                [673, 475, 513],
                [678, 0, 513],
                [741, 0, 513],
                [810, 0, 513],
                [919, 0, 513],
                [212, 513, 1023],
                [680, 513, 1023],
                [725, 513, 1023],
                [848, 513, 1023],
                [948, 0, 512],
                [949, 0, 512]
                ]
        else:
            []

        for column in bad_columns:
            x0 = column[0]
            y0 = column[1]
            yf = column[2]
            data = self.clean_column(data, x0, y0, yf)

        return data

    def clean_lines(self, data, header):
        """
        Clean the known bad lines that exists in most of SAMI's, SOI's or
        SIFS's data. This method is meant to be overwritten via inheritance.

        Args:

            data (numpy.ndarray) : A 2D numpy array that contains the data.

            header (astropy.io.fits.Header) : A header that will be updated.

        See also:

            Reducer.clean_column
            Reducer.clean_line
            Reducer.clean_lines
        """
        binning = header['CCDSUM'].split(' ')[0]
        binning = int(binning.strip())

        if binning == 4:
            bad_lines = [
                [166, 206, 282],
                [212, 258, 689],
                [214, 239, 688],
                [304, 345, 291],
                [386, 422, 454],
                [398, 422, 38],
                [477, 516, 490],
                [387, 429, 455],
                [574, 603, 494],
                [574, 603, 493],
                [640, 672, 388],
                [604, 671, 388],
                [698, 746, 198],
                [706, 634, 634],
                [772, 812, 354],
                [900, 938, 426],
                [904, 920, 396]
            ]

        else:
            bad_lines = []

        for line in bad_lines:
            x0 = line[0]
            xf = line[1]
            y = line[2]
            data = self.clean_line(data, x0, xf, y)

        return data

    @staticmethod
    def remove_central_bad_columns(data, header, prefix):
        """
        Remove central bad columns at the interface of the four extensions.

        Parameter
        ---------
            data : numpy.ndarray
                2D Array containing the data.
        """
        n_rows, n_columns = data.shape

        # Copy the central bad columns to a temp array
        temp_column = data[:, n_columns // 2 - 1:n_columns // 2 + 1]

        # Shift the whole image by two columns
        data[:, n_columns // 2 - 1:-2] = data[:, n_columns // 2 + 1:]

        # Copy the bad array in the end (right) of the image).
        data[:, -2:] = temp_column

        return data, header, prefix


class SifsReducer(SamiReducer):
    pass


class SoiReducer(Reducer):
    """
    SoiReducer

    This class holds all the methods used to join the extensions within a
    FITS file obtained with SOI.

    Parameters
    ----------
        zero_file : str
            The filename of the master zero that will be used in subtraction.

        clean : bool
            Clean bad collumns by taking the _median value of the pixels around
            them.

        cosmic_rays : bool
            Clean cosmic rays using LACosmic package. See noted bellow for
            reference.

        dark_file : str
            Master Dark's filename to be used for dark subtraction.

        debug : bool
            Turn on debug mode with lots of printing.

        flat_file : str
            Master Flat filename to be used for normalization.

        glow_file : str
            Master file that contains the lateral glowings sometimes present in
            SAMI's data.

        time : bool
            Divide each pixel's values by the exposure time and update header.

        verbose : bool
            Turn on verbose mode (not so talktive as debug mode).

    See also
    --------
        LACosmic - http://www.astro.yale.edu/dokkum/lacosmic/
    """

    @staticmethod
    def add_gap(data, header, interpolation_factor=10):
        """
        SOI has two detectors which are separated by 7.8 arcsec (or 102
        unbinned pixels). This method reads an merged array and adds the gap
        based on the detector's binning.

        Parameters
        ----------
            data : numpy.ndarray
                2D array with the data merged.

            header : astropy.io.fits.Header
                a header that contains the binning information on the 'CCDSUM'
                key.
        """
        if header['OBSTYPE'] == 'OBJECT':

            binning = header['CCDSUM']
            binning = int(binning.split()[0])

            gap_size = 7.8  # arcseconds
            pixel_scale = 0.0767  # arcsecond / pixel
            gap_pixel = int(round(gap_size / pixel_scale / binning, 0))

            nrow, ncol = data.shape

            data = _np.append(data, _np.zeros((nrow, gap_pixel)), axis=1)
            data[:, ncol // 2 + gap_pixel:] = data[:, ncol // 2:- gap_pixel]
            data[:, ncol // 2:ncol // 2 + gap_pixel] = 0

        return data, header

    def clean_columns(self, _data, _header):
        """
        Clean the known bad columns that exists in most of SAMI's data.

        Parameters
        ----------
            _data : numpy.ndarray
                A 2D numpy array that contains the data.

            _header : astropy.io.fits.Header
                a header that contains the binning information on the 'CCDSUM'
                key.

        See also
        --------
            SoiMerger.clean_column
            SoiMerger.clean_line
            SoiMerger.clean_lines
        """
        if not isinstance(_data, _np.ndarray):
            raise (TypeError, 'Please, use a np.array as input')
        if _data.ndim is not 2:
            raise (TypeError, 'Data contains %d dimensions while it was '
                              'expected 2 dimensions.')

        b = int(_header['CCDSUM'].strip().split(' ')[0])

        if b == 1:
            bad_columns = []
        elif b == 2:
            bad_columns = [
                [855, 0, 2047],
            ]
        elif b == 4:
            bad_columns = [
                [427, 0, 1023]
            ]
        else:
            logger.warning(
                'Skipping clean_columns for binning {} x {}'.format(b, b))
            bad_columns = []

        for column in bad_columns:
            x0 = column[0]
            y0 = column[1]
            yf = column[2]
            _data = self.clean_column(_data, x0, y0, yf)

        return _data

    def clean_lines(self, hdu_list):
        """
        Clean the known bad lines that exists in most of SAMI's, SOI's or
        SIFS's data. This method is meant to be overwritten via inheritance.

        Args:

            hdu_list (astropy.io.fits.HDUList)

        See also:

            Reducer.clean_column
            Reducer.clean_line
            Reducer.clean_lines
        """
        if not isinstance(hdu_list, _pyfits.HDUList):
            raise TypeError('Please, use a HDUList as input')

        if len(hdu_list) != 5:
            raise ValueError(
                "HDUList is expected to have 1 + 4 elements. Found {}".format(
                    len(hdu_list)))

        for i in range(1, len(hdu_list)):

            _data = hdu_list[i].data
            _hdr = hdu_list[i].header

            bad_lines = [
                # [166, 206, 282],
                # [212, 258, 689],
                # [214, 239, 688],
                # [304, 345, 291],
                # [386, 422, 454],
                # [398, 422, 38],
                # [477, 516, 490],
                # [387, 429, 455],
                # [574, 603, 494],
                # [574, 603, 493],
                # [640, 672, 388],
                # [604, 671, 388],
                # [698, 746, 198],
                # [706, 634, 634],
                # [772, 812, 354],
                # [900, 938, 426],
                # [904, 920, 396]
            ]

            for line in bad_lines:
                x0 = line[0]
                xf = line[1]
                y = line[2]
                _data = self.clean_line(_data, x0, xf, y)

            hdu_list[i].data = _data

        return hdu_list


def _normalize_data(data):
    """
    This method is intended to normalize flat data before it is applied to the
    images that are being reduced. A total of 1000 random points are used to
    estimate the _median level that will be used for normalization.

    Args:

        data (numpy.ndarray) : Data that will be normalized

    Returns:
        norm_data (numpy.ndarray) : Normalized data.
    """
    sample = _np.random.randint(0, high=data.size - 1, size=1000)
    mode = stats.mode(data.ravel()[sample])[0]

    return data / mode
