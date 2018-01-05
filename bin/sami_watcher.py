#!/usr/bin/env python 
# -*- coding: utf8 -*-

import soar_sami

__author__ = 'Bruno Quint'
__version__ = soar_sami.version
print(__version__)

test_path = '/home/bquint/Data/SAM/20160927/RAW'
soar_sami.watcher.watch(test_path)
