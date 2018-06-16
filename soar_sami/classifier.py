
import threading
import numpy as np
import pandas as pd
import os

# TODO - Implement the same when we have PsycoPG2 installed
import sqlite3 as sql

from astropy.io import fits
from datetime import datetime
from glob import glob

from .io.sami_log import SAMILog
from .io.sami_data import SAMI_Data

__author__ = 'Bruno Quint'
logger = SAMILog(__name__, debug=True)

COLUMNS = {
    #'id': "int64",
    'filename': "str",
    'date_created': "str",
    'time_created': "str",
    # 'ra': "float64",
    # 'dec': "float64",
    # 'ccdsum': "str",
    # 'obs_type': "str",
    # 'obs_name' : "str",
    # 'obs_comments': "str",
    # 'exp_time' : "float64",
    # 'filter': "str",
    # 'merged': "bool",
    # 'bias_subtracted': "bool",
    # 'bias_name': "str",
    # 'flat_normalized': "bool",
    # 'flat_name': "str",
    # 'combined': "bool",
    # 'astrometric_solution_found': "bool"
}


def classify(path, pid, date):
    """
    Args:

        path (string): path to the folder that contains the data to be reduced.

        pid (string): Program ID.

        date (string): observation date in the following format YYYY-MM-DD where
            YYYY, MM, DD are all integers.

    """

    database_name = '.temp.db'

    logger.debug('Starting to create a DataFrame.')
    df = pd.DataFrame(columns=COLUMNS.keys())

    for c in df.columns:
        df[c] = df[c].astype(COLUMNS[c])

    logger.debug(
        'Walking through the files within the folder {:s}.'.format(path))

    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if os.path.splitext(name)[-1] in ['.fits', '.fits.bz2']:

                logger.debug('Update database {:s} with file {:s}'.format(
                    database_name, name))

                ad = SAMI_Data(os.path.join(root, name))
                s = ad.to_series()


    return 0




class DataClassifier(threading.Thread):

    def __init__(self, path):

        super(DataClassifier, self).__init__()

        self.path = path

    def run(self):

        return 0



# # Create table
#
# list_of_bias = []
# list_of_flats = []
# list_of_objects = []
#
# for filename in glob(os.path.join(path, '*.fits')):
#     print(filename)
#     ccd = CCDData(filename, unit=u.adu)
#     print(ccd.header)
#     if ccd.header['OBSTYPE'] == 'BIAS':
#         list_of_bias.append(ccd)
#     elif 'FLAT' in ccd.header['OBSTYPE']:
#         list_of_flats.append(ccd)
#     elif ccd.header['OBSTYPE'] == 'OBJECT':
#         list_of_objects.append(ccd)
#
#     print('Ok.')
#
# print(list_of_bias)
# print(list_of_flats)
# print(list_of_objects)
#
#
