
import threading
import sqlite3
import pandas as pd
import os

__author__ = 'Bruno Quint'

def classify(path):

    create_database(path, '.temp.db')

    return 0


def create_database(path, database_name):

    columns = [
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
        ''
    ]

    conn = sqlite3.connect(os.path.join(path, database_name))
    cur = conn.cursor()

    df = pd.DataFrame(columns=columns)


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
