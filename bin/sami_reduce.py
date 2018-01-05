#!/usr/bin/env python 
# -*- coding: utf8 -*-

import soar_sami

__author__ = 'Bruno Quint'
__version__ = soar_sami.version

# TODO - Enter input path as command line argument.
# test_path = '/home/bquint/Data/SAM/20160927/RAW'  # soarbr3
test_path = '/Users/Bruno/Data/20170402/'  # qbook

# TODO - Check if input path exists

soar_sami.classifier.classify(test_path)
