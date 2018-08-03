import numpy as _np


def iraf2python(my_string):
    """
    Parse a string containing [XX:XX, YY:YY] to pixels.

    Parameter
    ---------
        my_string : str
    """
    my_string = my_string.strip()
    my_string = my_string.replace('[', '')
    my_string = my_string.replace(']', '')
    x, y = my_string.split(',')
    x = x.split(':')
    y = y.split(':')

    x = _np.array(x, dtype=int)
    y = _np.array(y, dtype=int)

    x[0] -= 1
    y[0] -= 1

    return x, y


def python2iraf(x1, x2, y1, y2):
    """
    Convert from Pythonic indexes to IRAFonic indexes.

    Args:
        x1: int
        x2: int
        y1: int
        y2: int

    Returns:
        section : str
    """
    s = '[{:1d}:{:1d}, {:1d}:{:1d}]'.format(x1 + 1, x2, y1 + 1, y2)
    return s