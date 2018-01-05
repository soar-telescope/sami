# -*- coding: utf-8 -*-
"""
v0.0.0 - Initial Version.
"""

api = 0
feature = 0
bug = 0

month = 12
year = 2017

__str__ = "v{api:d}.{feature:d}.{bug:d} {month:d}, {year:d}".format(**locals())
