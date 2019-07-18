#!/usr/bin/env python
# NOTE: this is the right shebang, compatible with virtual / conda environments
# https://stackoverflow.com/questions/6908143/should-i-put-shebang-in-python-scripts-and-what-form-should-it-take

# NOTE: This script cannot be named clfd.py, because that makes any statement 
# 'import clfd.X' fail

import sys
import argparse
import logging
import json
import os

import clfd
import clfd.interfaces
from clfd.apps import cleanup_main

log = logging.getLogger("clfd")

help_formatter = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=16)

def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=help_formatter, #argparse.ArgumentDefaultsHelpFormatter,
        description="Apply smart RFI cleaning algorithms to folded data archives. \
        Version: {}".format(clfd.__version__)
    )
    parser.add_argument(
        "--fmt",
        type=str,
        choices=["psrchive"],
        default="psrchive",
        help="Input file format",
    )
    parser.add_argument(
        "-z",
        "--zapfile",
        type=str,
        default=None,
        help="Optional text file that specifies a list of frequency channels to forcibly mask \
        and exclude from the analysis. Every line of this file must be a channel index to mask.",
    )
    parser.add_argument(
        "-f",
        "--features",
        type=str,
        action="store",
        nargs="*",
        default=["std","ptp","lfamp"],
        help="List of profile features to use for the profile masking algorithm, separated by spaces.",
    )
    parser.add_argument(
        "--qmask",
        type=float,
        default=2.0,
        help="Tukey's rule parameter for the profile masking algorithm. This parameter is the number of \
        inter-quartile ranges that define the inlier range of a distribution.",
    )
    parser.add_argument(
        "--despike",
        action="store_true",
        default=False,
        help="Apply the zero DM spike removal algorithm, i.e. find outliers in the zero DM time-phase plot \
        and replace them by appropriate values (inferred from the data itself) across the frequency dimension. \
        Note that any channels specified by the optional zapfile are excluded from the analysis \
        and left untouched. \
        WARNING: may negatively affect very bright individual pulses from a low-DM pulsar. Can also fail \
        in particularly bad RFI environments. In doubt, avoid using this option and if you do, check the \
        output carefully.",
    )
    parser.add_argument(
        "--qspike",
        type=float,
        default=4.0,
        help="Tukey's rule parameter for the zero DM spike removal algorithm.",
    )
    parser.add_argument(
        "-e",
        "--ext",
        type=str,
        default="clfd",
        help="Additional extension given to the clean output files.",
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        default=1,
        help="Number of parallel processes to be used.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        default=False,
        help="If specified, do NOT save HDF5 cleanup report(s). If the \
        pytables python module is not installed, you will have to use this option.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=clfd.__version__,
        help="Print version number and exit",
    )
    parser.add_argument("filenames", type=str, nargs="+", help="Input file(s)")
    args = parser.parse_args()
    return args


def main():
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)5s - %(asctime)s] %(message)s")

    args = parse_arguments()
    log.debug("Called with arguments: {!s}".format(vars(args)))

    # Format keyword arguments properly for the cleanup_main() function
    kw = dict(vars(args))
    kw.pop('filenames')

    kw.pop('no_report')
    kw['report'] = not args.no_report
    cleanup_main(args.filenames, **kw)

    
if __name__ == "__main__":
    main()
