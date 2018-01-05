
import threading
import pandas as pd
import os

# TODO - Implement the same when we have PsycoPG2 installed
import sqlite3 as sql

from astropy.io import fits
from datetime import datetime
from glob import glob

from .io import sami_log

__author__ = 'Bruno Quint'
logger = sami_log.SAMILog(__name__, debug=True)


def classify(path):

    create_database(path, '.temp.db')

    return 0


def create_database(path, database_name):

    logger.debug('Starting to create a database.')

    columns = [
        'id',
        'filename',
        'date_created',
        'time_created',
        'ra',
        'dec',
        'ccdsum',
        'obs_type',
        'obs_name',
        'obs_comments',
        'exp_time',
        'filter',
        'merged',
        'bias_subtracted',
        'flat_normalized',
        'combined',
        'astrometric_solution_found'
    ]

    logger.debug('Connecting to the database: {:s}'.format(database_name))
    conn = sql.connect(os.path.join(path, database_name))
    cur = conn.cursor()

    logger.debug(
        'Walking through the files within the folder {:s}.'.format(path))

    df = pd.DataFrame(columns=columns)

    logger.debug('Walking through the path recursively.')

    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if os.path.splitext(name)[-1] in ['.fits', '.fits.bz2']:
                logger.debug('  {:s}'.format(os.path.join(root, name)))

                h = fits.getheader(os.path.join(root, name))

    conn.close()


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
