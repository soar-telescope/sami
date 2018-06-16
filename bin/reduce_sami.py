#!/usr/bin/env python 
# -*- coding: utf8 -*-

import soar_sami

from soar_sami.io import sami_log

__author__ = 'Bruno Quint'
__version__ = soar_sami.version

# TODO - Enter input path as command line argument.
# test_path = '/home/bquint/Data/SAM/20160927/RAW'  # soarbr3
test_path = '/Users/Bruno/Data/20170402/'  # qbook
program_id = 'SO2025X-007'
date = 'YYYY-MM-YY'

# TODO - Check if input path exists
logger = sami_log.SAMILog(__name__, debug=True)
logger.info('SAMI Pipeline - Running on folder: {:s}'.format(test_path))


def reduce_sami():
    table = soar_sami.classifier.classify(test_path, program_id, date)
    soar_sami.data_reduction.sami_reduce(table)
