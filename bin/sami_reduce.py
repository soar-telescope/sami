#!/usr/bin/env python 
# -*- coding: utf8 -*-

__author__ = 'Bruno Quint'


import soar_sami

test_path = '/home/bquint/Data/SAM/20160927/RAW' # soarbr3
test_path = '/Users/Bruno/Data/20170402/'

soar_sami.classifier.classify(test_path)
