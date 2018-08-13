#!/usr/bin/env python
# -*- coding: utf8 -*-

import ccdproc
import pandas as pd
import glob
import numpy
import os

from soar_simager.io import pyfits
from soar_simager.io.logging import get_logger
from soar_simager.tools import version
from soar_simager.data_reduction import reduce, combine

astropy_logger = get_logger('astropy')
astropy_logger.setLevel('NOTSET')

ccdproc_logger = get_logger('ccdproc')
ccdproc_logger.setLevel('NOTSET')

log = get_logger('soidr')
log.propagate = False

__author__ = 'Bruno Quint'

KEYWORDS = ["OBSTYPE", "FILTERS", "CCDSUM"]


def build_table(list_of_files):
    """
    Return a pandas.DataFrame used to organize the pipeline.

    Args:
        list_of_files (list) : list of files to be included in the dataframe.

    Returns:
        table (pandas.Dataframe) : a dataframe with information needed for the
        pipeline.
    """
    log.info('Reading raw files')

    table = pd.DataFrame(
        columns=[
            'filename',
            'instrume',
            'obstype',
            'filters',
            'filter1',
            'filter2',
            'binning',
            'flat_file',
            'zero_file',
        ]
    )

    list_of_files.sort()
    for _file in list_of_files:

        try:
            hdu = pyfits.open(_file)
        except OSError:
            log.warning("Could not read file: {}".format(_file))
            continue

        if numpy.std(hdu[1].data.ravel()) == 0:
            log.warning("Bad data found on file: {}".format(_file))
            continue

        row = pd.Series(data={
            'filename': _file,
            'obstype': hdu[0].header['obstype'],
            'instrume': hdu[0].header['instrume'].strip().upper(),
            'filters': hdu[0].header['filters'],
            'filter1': hdu[0].header['filter1'],
            'filter2': hdu[0].header['filter2'],
            'binning': hdu[1].header['ccdsum'].strip(),
            'flat_file': None,
            'zero_file': None,
        })

        table = table.append(row, ignore_index=True, sort=True)

    return table


def create_reduced_folder(path):
    """
    Check if directory that will host the processed data exists or not. If not,
    creates it.

    Args:
        path (str) : string with the directory for processed data.
    """

    if os.path.exists(path):
        log.warning('Skipping existing directory: {}'.format(path))
    else:
        log.info('Creating directory for reduced data: {}'.format(path))

    os.makedirs(path, exist_ok=True)

    return path


def get_binning_used(table):
    """
    Get all the binning modes used during the observation night.

    Args:
        table (pandas.DataFrame) : table used in the pipeline.

    Returns:
        list_of_binning (list) : list with the different binning used during
        observation.
    """

    list_of_binning = []
    for row in table:
        if row['binning'] not in list_of_binning:
            list_of_binning.append(row['binning'])
            log.info('Found new binning mode: {}'.format(
                row['binning'][0], row['binning'][1]))

    return list_of_binning


def process_flat_files(df, red_path):
    """
    Args:
        df (pandas.DataFrame) : a data-frame containing the all the data being
        processed.
        red_path (str) : the path where the reduced data is stored.

    Returns:
        updated_table (pandas.DataFrame) : an updated data-frame where each
        file now is attached to the corresponding master Zero file.
    """
    log.info('Processing FLAT files (SFLAT + DFLAT)')
    soi_merger = reduce.SoiReducer()
    soi_merger.clean = True

    binning = df.binning.unique()

    for b in binning:

        bx, by = b.split(' ')
        log.info('Processing FLAT files with binning: {} x {}'.format(bx, by))

        mask1 = (df.obstype.values == 'SFLAT') | (df.obstype.values == 'DFLAT')
        mask2 = df.binning.values == b
        flat_df = df.loc[mask1 & mask2]

        filters_used = flat_df.filters.unique()

        for _filter in filters_used:

            log.info('Processing FLATs for filter: {}'.format(_filter))

            filter_flat_df = flat_df.loc[flat_df.filters.values == _filter]
            filter_flat_df.sort_values('filename')

            log.info(
                'Filter Wheel 1: {}'.format(filter_flat_df.filter1.unique()[0]))

            log.info(
                'Filter Wheel 2: {}'.format(filter_flat_df.filter2.unique()[0]))

            flat_list = []
            for index, row in filter_flat_df.iterrows():

                soi_merger.zero_file = row.zero_file
                soi_merger.flat_file = None
                flat_file = row.filename
                prefix = soi_merger.get_prefix()

                path, fname = os.path.split(flat_file)
                output_flat = os.path.join(red_path, prefix + fname)
                flat_list.append(prefix + fname)

                if os.path.exists(output_flat):
                    log.warning(
                        'Skipping existing FLAT file: {}'.format(output_flat))
                    continue

                log.info('Processing FLAT file: {}'.format(flat_file))

                d = soi_merger.merge(flat_file)
                h = soi_merger.get_header(flat_file)

                d, h, p = soi_merger.__reduce(d, h)
                pyfits.writeto(output_flat, d, h)

            flat_list_name = os.path.join(
                red_path, "1FLAT_{}x{}_{}".format(bx, by, _filter))

            with open(flat_list_name, 'w') as flat_list_buffer:
                for flat_file in flat_list:
                    flat_list_buffer.write('{:s}\n'.format(flat_file))

            master_flat = flat_list_name + '.fits'

            if os.path.exists(master_flat):
                log.warning(
                    'Skipping existing MASTER FLAT: {:s}'.format(master_flat))
            else:
                log.info('Writing master FLAT to file: {}'.format(master_flat))

            flat_combine_files = [os.path.join(red_path, f) for f in flat_list]

            flat_combine = combine.FlatCombine(
                 input_list=flat_combine_files, output_file=master_flat)

            flat_combine.run()

            mask1 = df['obstype'].values == 'OBJECT'
            mask2 = df['binning'].values == b
            df.loc[mask1 & mask2, 'flat_file'] = master_flat

    return df


def process_object_files(df, red_path):
    """
    Args:
        df (pandas.DataFrame) : a data-frame containing the all the data being
        processed.
        red_path (str) : the path where the reduced data is stored.

    Returns:
        updated_table (pandas.DataFrame) : an updated data-frame where each
        file now is attached to the corresponding master Zero file.
    """
    soi_merger = reduce.SoiReducer()
    soi_merger.cosmic_rays = True
    soi_merger.clean = True

    log.info('Processing OBJECT files.')

    object_df = df.loc[df.obstype.values == 'OBJECT']

    for index, row in object_df.iterrows():

        soi_merger.zero_file = row.zero_file
        soi_merger.flat_file = row.flat_file
        obj_file = row.filename

        path, fname = os.path.split(obj_file)
        prefix = soi_merger.get_prefix()
        output_obj_file = os.path.join(path, 'RED', prefix + fname)

        if os.path.exists(output_obj_file):
            log.warning(
                'Skipping existing OBJECT file: {}'.format(output_obj_file))
            continue

        log.info('Processing OBJECT file: {}'.format(obj_file))

        d = soi_merger.merge(obj_file)
        h = soi_merger.get_header(obj_file)
        h = soi_merger.create_wcs(d, h)

        d, h, p = soi_merger.__reduce(d, h)

        pyfits.writeto(output_obj_file, d, h)

    return df


def process_zero_files(df, red_path):
    """
    Args:
        df (pandas.DataFrame) : a data-frame containing the all the data being
        processed.
        red_path (str) : the path where the reduced data is stored.

    Returns:
        updated_table (pandas.DataFrame) : an updated data-frame where each
        file now is attached to the corresponding master Zero file.
    """
    soi_merger = reduce.SoiReducer()

    binning = df.binning.unique()

    log.debug('Binning formats found in data: ')
    for b in binning:
        log.debug('   {:s}'.format(b))

    for b in binning:

        bx, by = b.split(' ')
        log.info('Processing ZERO files with binning: {} x {}'.format(bx, by))

        mask1 = df.obstype.values == 'ZERO'
        mask2 = df.binning.values == b

        zero_table = df.loc[mask1 & mask2]
        zero_table = zero_table.sort_values('filename')

        zero_list = []
        for index, row in zero_table.iterrows():

            soi_merger.zero_file = None
            soi_merger.flat_file = None
            soi_merger.clean = True
            zero_file = row.filename

            path, fname = os.path.split(zero_file)
            prefix = soi_merger.get_prefix()
            output_zero_file = os.path.join(red_path, prefix + fname)

            zero_list.append(prefix + fname)

            if os.path.exists(output_zero_file):
                log.warning('Skipping existing file: {}'.format(
                    output_zero_file))
                continue

            log.info('Processing ZERO file: {}'.format(zero_file))

            data = soi_merger.merge(zero_file)
            header = soi_merger.get_header(zero_file)

            log.debug('Data format: {0[0]:d} x {0[1]:d}'.format(data.shape))

            data, header, prefix = soi_merger.__reduce(data, header)
            pyfits.writeto(output_zero_file, data, header)

        zero_list_name = os.path.join(red_path, "0Zero{}x{}".format(bx, by))

        with open(zero_list_name, 'w') as zero_list_buffer:
            for zero_file in zero_list:
                zero_list_buffer.write('{:s}\n'.format(zero_file))

        log.info('Combining ZERO files.')
        master_zero = zero_list_name + '.fits'

        if os.path.exists(master_zero):
            log.warning(
                'Skipping existing MASTER ZERO: {:s}'.format(master_zero))

        else:

            log.info("Writing master zero to: {}".format(master_zero))
            zero_combine_files = [os.path.join(red_path, f) for f in zero_list]

            zero_combine = combine.ZeroCombine(input_list=zero_combine_files,
                                               output_file=master_zero)
            zero_combine.run()
            log.info('Done.')

        mask1 = df['obstype'].values != 'ZERO'
        mask2 = df['binning'].values == b
        df.loc[mask1 & mask2, 'zero_file'] = master_zero

    return df


def reduce(path, debug=False, quiet=False):

    if debug:
        log.setLevel('DEBUG')
    elif quiet:
        log.setLevel('NOTSET')
    else:
        log.setLevel('INFO')

    log.info('SOAR Imager Data-Reduction Pipeline')
    log.info('Version {}'.format(version.__str__))

    reduced_path = create_reduced_folder(os.path.join(path, 'RED'))

    list_of_files = glob.glob(os.path.join(path, '*.fits'))

    table = build_table(list_of_files)

    table = filter_files(table)

    table = process_zero_files(table, reduced_path)

    table = process_flat_files(table, reduced_path)

    process_object_files(table, reduced_path)


def filter_files(df):
    """
    Remove files that are not obtained with SOI from the data-frame.

    Args:
        df (pandas.DataFrame)

    Returns:
        filtered_df (pandas.DataFrame)
    """
    log.info('Checking how many files obtained with SOI')

    n_total = len(df.index)
    df = df[df.instrume == 'SOI']
    n_processed = len(df.index)
    n_rejected = n_total - n_processed

    log.info('Number of files to be processed: {:d}'.format(n_processed))
    log.info('Number of files rejected: {:d}'.format(n_rejected))

    return df
