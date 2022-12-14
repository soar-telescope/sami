#!/usr/bin/env python
# -*- coding: utf8 -*-

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

log = get_logger('samidr')
log.propagate = False

__author__ = 'Bruno Quint'

KEYWORDS = ["OBSTYPE", "FILTERS", "CCDSUM"]


def data_reduction(path, debug=False, quiet=False):

    """
    Main method for SAMI data reduction pipeline.

    Args:
         path (str) : path to the directory which contains the data.

         debug (bool, optional) : enable debug mode (default = False).

         quiet (bool, optional) : disable printing on screen (default = False).
    """

    if debug:
        log.setLevel('DEBUG')
    elif quiet:
        log.setLevel('NOTSET')
    else:
        log.setLevel('INFO')

    log.info('SAMI Data-Reduction Pipeline')
    log.info('Version {}'.format(version.__str__))

    reduced_path = create_reduced_folder(os.path.join(path, 'RED'))

    list_of_files = glob.glob(os.path.join(path, '*.fits'))

    dataframe = build_table(list_of_files)

    dataframe = filter_files(dataframe)

    dataframe = process_zero_files(dataframe, reduced_path)

    dataframe = process_dark_files(dataframe, reduced_path)

    dataframe = process_flat_files(dataframe, reduced_path)

    process_object_files(dataframe, reduced_path)

    write_dataframe_to_html(dataframe)

    log.info("All done.")

    
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
            'dark_file',
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
            'dark_file': None,
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

 
def filter_files(df):
    """
    Remove files that are not obtained with SAMI from the data-frame.

    Args:
        df (pandas.DataFrame)

    Returns:
        filtered_df (pandas.DataFrame)
    """
    log.info('Checking how many files obtained with SAMI')

    n_total = len(df.index)
    df = df[df.instrume == 'SAM']
    n_processed = len(df.index)
    n_rejected = n_total - n_processed

    log.info('Number of files to be processed: {:d}'.format(n_processed))
    log.info('Number of files rejected: {:d}'.format(n_rejected))

    return df

 
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


def process_dark_files(df, red_path):
    """
    Args:

        df (pandas.DataFrame) : a data-frame containing the all the data being
        processed.

        red_path (str) : the path where the reduced data is stored.

    Returns:

        updated_table (pandas.DataFrame) : an updated data-frame where each
        file now is attached to the corresponding master Zero file.

    """
    sami_pipeline = reduce.SamiReducer()

    binning = df.binning.unique()

    for b in binning:

        bx, by = b.split(' ')
        log.info('Processing DARK files with binning: {} x {}'.format(bx, by))

        mask1 = df.obstype.values == 'DARK'
        mask2 = df.binning.values == b

        dark_table = df.loc[mask1 & mask2]
        dark_table = dark_table.sort_values('filename')

        dark_list = []
        for index, row in dark_table.iterrows():

            sami_pipeline.cosmic_rays = True
            sami_pipeline.dark_file = None
            sami_pipeline.flat_file = None
            sami_pipeline.time = True
            sami_pipeline.zero_file = row.zero_file

            dark_file = row.filename

            path, fname = os.path.split(dark_file)
            prefix = sami_pipeline.get_prefix()
            output_dark_file = os.path.join(red_path, prefix + fname)

            dark_list.append(prefix + fname)

            if os.path.exists(output_dark_file):
                log.warning('Skipping existing file: {}'.format(
                    output_dark_file))
                continue

            log.info('Processing DARK file: {}'.format(dark_file))

            hdul = pyfits.open(dark_file)
            data, header, prefix = sami_pipeline.reduce(hdul)
            pyfits.writeto(output_dark_file, data.value, header=header)

        if len(dark_list) == 0:
            continue

        dark_list_name = os.path.join(red_path, "1Dark{}x{}".format(bx, by))

        with open(dark_list_name, 'w') as dark_list_buffer:
            for dark_file in dark_list:
                dark_list_buffer.write('{:s}\n'.format(dark_file))

        log.info('Combining ZERO files.')
        master_dark = dark_list_name + '.fits'

        if os.path.exists(master_dark):
            log.warning(
                'Skipping existing MASTER ZERO: {:s}'.format(master_dark))

        else:

            log.info("Writing master zero to: {}".format(master_dark))
            dark_combine_files = [os.path.join(red_path, f) for f in dark_list]

            dark_combine = combine.DarkCombine(input_list=dark_combine_files,
                                               output_file=master_dark)
            dark_combine.run()
            log.info('Done.')

        mask1 = df['obstype'].values != 'DARK'
        mask2 = df['binning'].values == b
        df.loc[mask1 & mask2, 'dark_file'] = master_dark

    return df


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
    sami_pipeline = reduce.SamiReducer()

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

                sami_pipeline.zero_file = row.zero_file
                sami_pipeline.dark_file = row.dark_file
                sami_pipeline.flat_file = None
                flat_file = row.filename
                prefix = sami_pipeline.get_prefix()

                path, fname = os.path.split(flat_file)
                output_flat = os.path.join(red_path, prefix + fname)
                flat_list.append(prefix + fname)

                if os.path.exists(output_flat):
                    log.warning(
                        'Skipping existing FLAT file: {}'.format(output_flat))
                    continue

                log.info('Processing FLAT file: {}'.format(flat_file))

                hdul = pyfits.open(flat_file)
                data, header, prefix = sami_pipeline.reduce(hdul)
                pyfits.writeto(output_flat, data.value, header=header)

            if len(flat_list) == 0:
                continue

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
            mask3 = df['filters'].values == _filter
            df.loc[mask1 & mask2 & mask3, 'flat_file'] = master_flat

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
    sami_pipeline = reduce.SamiReducer()
    sami_pipeline.cosmic_rays = True

    log.info('Processing OBJECT files.')

    object_df = df.loc[df.obstype.values == 'OBJECT']

    for index, row in object_df.iterrows():

        sami_pipeline.zero_file = row.zero_file
        sami_pipeline.dark_file = row.dark_file
        sami_pipeline.flat_file = row.flat_file
        obj_file = row.filename

        path, fname = os.path.split(obj_file)
        prefix = sami_pipeline.get_prefix()
        output_obj_file = os.path.join(red_path, prefix + fname)

        if os.path.exists(output_obj_file):
            log.warning(
                'Skipping existing OBJECT file: {}'.format(output_obj_file))
            continue

        log.info('Processing OBJECT file: {}'.format(obj_file))

        hdul = pyfits.open(obj_file)
        data, header, prefix = sami_pipeline.reduce(hdul)
        pyfits.writeto(output_obj_file, data.value, header=header)

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
    sami_pipeline = reduce.SamiReducer()
    sami_pipeline.cosmic_rays = True

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

            sami_pipeline.zero_file = None
            sami_pipeline.flat_file = None
            zero_file = row.filename

            path, fname = os.path.split(zero_file)
            prefix = sami_pipeline.get_prefix()
            output_zero_file = os.path.join(red_path, prefix + fname)

            zero_list.append(prefix + fname)

            if os.path.exists(output_zero_file):
                log.warning('Skipping existing file: {}'.format(
                    output_zero_file))
                continue

            log.info('Processing ZERO file: {}'.format(zero_file))

            hdul = pyfits.open(zero_file)
            data, header, prefix = sami_pipeline.reduce(hdul)
            pyfits.writeto(output_zero_file, data.value, header=header)

        if len(zero_list) == 0:
                continue

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


def write_dataframe_to_html(df):
    """
    Writes the dataframe as a HTML file for debugging.

    Parameters
    ----------
        df : pandas.DataFrame
    """
    html_file_name = 'sami_reduce.html'

    with open(html_file_name, 'w') as f:
        df.to_html(
            buf=f,
            table_id='sami_reduce',
            columns=[
                'filename',
                'instrume',
                'binning',
                'filter1',
                'filter2',
                'filters',
                'obstype',
                'zero_file',
                'dark_file',
                'flat_file',
            ]
        )

    log.info("Saved dataframe to file: {}".format(html_file_name))
