# -*- coding: utf-8 -*-
"""
v0.0.0 - Initial Version.
v0.1.0 - Pipeline actually running.
       - To Do: Improve LaCosmic parameters.
"""

api = 0
feature = 1
bug = 0

month = 6
year = 2018

__str__ = "v{api:d}.{feature:d}.{bug:d} {month:d}, {year:d}".format(**locals())
