#!/usr/bin/env python 
# -*- coding: utf8 -*-

from __future__ import absolute_import, division, print_function

from .io.sami_log import SAMILog

__author__ = 'Bruno Quint'

log = SAMILog(__name__, verbose=True)


def sami_reduce():
    log.info('My info message')
    return


if __name__ == '__main__':
    sami_reduce()