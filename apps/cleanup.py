import argparse
import logging
import json
import os

import clfd
import clfd.interfaces

from functions import cleanup_main

log = logging.getLogger("clfd")

def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
        WARNING: may negatively affect very bright individual pulses from a low-DM pulsar.",
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
        help="Extension given to the clean output files.",
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        default=1,
        help="Number of parallel processes to be used.",
    )
    parser.add_argument("filenames", type=str, nargs="+", help="Input file(s)")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s - %(asctime)s] %(message)s")

    args = parse_arguments()
    log.debug("Called with arguments: {!s}".format(vars(args)))

    kw = dict(vars(args))
    kw.pop('filenames')
    cleanup_main(args.filenames, **kw)
    
