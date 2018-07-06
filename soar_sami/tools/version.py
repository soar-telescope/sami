# -*- coding: utf-8 -*-
"""
v0.0.0 - Initial Version.
v0.1.0 - Pipeline actually running.
       - To Do: Improve LaCosmic parameters.
v0.1.1 - Fixed bug related to master bias and flat names.
       - Added prefix to reduced data.
v0.1.2 - Fixed bug related to the logging system.
v0.1.3 - Fixed bug that prevented reducing some filters.
       - At some point, it is useful to have the full filter name.
v0.1.4 - Skipping existing ZERO and FLAT frames.
       - WCS is added to objects when merging amplifiers.
"""

api = 0
feature = 1
bug = 4

month = 6
year = 2018

__str__ = "{api:d}.{feature:d}.{bug:d} {month:d}, {year:d}".format(**locals())
