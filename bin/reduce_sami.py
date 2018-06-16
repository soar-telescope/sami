#!/usr/bin/env python 
# -*- coding: utf8 -*-

from soar_sami.data_reduction import reduce
from soar_sami.tools import version

__author__ = 'Bruno Quint'
__version__ = version


def main():
    args = _parse_arguments()
    reduce.reduce_sami(args.path)


def _parse_arguments():
    """
    Parse the argument given by the user in the command line.

    Returns
    -------
        pargs : Namespace
        A namespace containing all the parameters that will be used for SAMI
        XJoin.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Perform data reduction on images obtained with SAMI."
    )

    parser.add_argument('path', type=str,
                        help="Path containing the data to be reduced.")

    return parser.parse_args()


if __name__ == "__main__":
    main()