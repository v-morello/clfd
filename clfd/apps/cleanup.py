import argparse
import logging
import multiprocessing
import os

import clfd

from .functions import Worker, load_zapfile

log = logging.getLogger("clfd")


def parse_arguments():
    def outdir(path):
        """Function that checks the outdir argument"""
        if not os.path.isdir(path):
            msg = "Specified output directory {!r} does not exist".format(path)
            raise argparse.ArgumentTypeError(msg)
        return path

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Apply smart RFI cleaning algorithms to folded data archives. \
        Version: {}".format(
            clfd.__version__
        ),
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=outdir,
        default=None,
        help="Output directory for the data products. If not specified (by default), the products \
        corresponding to a given input file are written in the same directory as that file.",
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
        default=["std", "ptp", "lfamp"],
        help="List of profile features to use for the profile masking algorithm, separated by \
        spaces.",
    )
    parser.add_argument(
        "--qmask",
        type=float,
        default=2.0,
        help="Tukey's rule parameter for the profile masking algorithm. This parameter is the \
        number of inter-quartile ranges that define the inlier range of a distribution.",
    )
    parser.add_argument(
        "--despike",
        action="store_true",
        default=False,
        help="Apply the zero DM spike removal algorithm, i.e. find outliers in the zero DM \
        time-phase plot and replace them by appropriate values (inferred from the data itself) \
        across the frequency dimension. \
        Note that any channels specified by the optional zapfile are excluded from the analysis \
        and left untouched. \
        WARNING: may negatively affect very bright individual pulses from a low-DM pulsar. \
        Can also fail in particularly bad RFI environments. In doubt, avoid using this option \
        and if you do, check the output carefully.",
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
    parser.add_argument("archives", type=str, nargs="+", help="Input PSRCHIVE archive(s)")
    args = parser.parse_args()
    return args


def main():
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)5s - %(asctime)s] %(message)s")

    args = parse_arguments()
    log.debug("Called with arguments: {!s}".format(vars(args)))
    log.debug("Files to process: {:d}".format(len(args.archives)))

    zap_channels = load_zapfile(args.zapfile) if args.zapfile else []
    log.debug(f"Ignoring {len(zap_channels)} channel indices: {zap_channels}")

    worker = Worker(
        {
            "zap_channels": zap_channels,
            "outdir": args.outdir,
            "features": args.features,
            "qmask": args.qmask,
            "despike": args.despike,
            "qspike": args.qspike,
            "ext": args.ext,
            "report": not args.no_report,
        }
    )

    log.info("Using {:d} parallel processes".format(args.processes))
    with multiprocessing.Pool(processes=args.processes) as pool:
        pool.map(worker, args.archives)
        pool.close()
        pool.join()
    log.info("Done.")


if __name__ == "__main__":
    main()
