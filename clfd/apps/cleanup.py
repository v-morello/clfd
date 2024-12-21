import argparse
import logging
import logging.config
import multiprocessing
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from clfd import __version__
from clfd.features import available_features

from .functions import Worker, load_zapfile

log = logging.getLogger("clfd")


def make_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "Apply smart RFI cleaning algorithms to folded data archives. "
            "Version: {}".format(__version__)
        ),
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=validate_output_dir,
        default=None,
        help=(
            "Output directory for the data products. If not specified, the "
            "products corresponding to a given input file are written in the "
            "same directory as that file."
        ),
    )
    parser.add_argument(
        "-z",
        "--zapfile",
        type=str,
        default=None,
        help=(
            "Optional text file with a list of frequency channels "
            "to forcibly mask and exclude from the analysis. Every line "
            "must be a channel index to mask."
        ),
    )
    parser.add_argument(
        "-f",
        "--features",
        type=str,
        action="store",
        choices=sorted(available_features().keys()),
        metavar="FEAT_NAME",
        nargs="+",
        default=["std", "ptp", "lfamp"],
        help=(
            "List of profile features to use for the profile masking "
            "algorithm, separated by spaces. "
            f"Choices: {sorted(available_features().keys())}"
        ),
    )
    parser.add_argument(
        "-q",
        "--qmask",
        type=float,
        default=2.0,
        help=(
            "Tukey's rule parameter for the profile masking algorithm. "
            "Larger values result in fewer outliers."
        ),
    )
    parser.add_argument(
        "--despike",
        action="store_true",
        default=False,
        help=(
            "Apply the time-phase spike subtraction algorithm. "
            "WARNING: can attenuate / remove bright individual pulses "
            "from a low-DM pulsar. Can also fail in particularly bad RFI "
            "environments."
        ),
    )
    parser.add_argument(
        "--qspike",
        type=float,
        default=4.0,
        help=(
            "Tukey's rule parameter for the time-phase spike subtraction "
            "algorithm. Larger values result in fewer outliers."
        ),
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        default=default_num_processes(),
        help="Number of parallel processes to use.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        default=False,
        help="Do not save reports and associated plots.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print version number and exit",
    )
    parser.add_argument(
        "archives",
        type=str,
        nargs="+",
        help="Input PSRCHIVE archive(s)",
    )
    return parser


def default_num_processes() -> int:
    n = os.cpu_count()
    return n if n is not None else 1


def validate_output_dir(path):
    """Function that checks the outdir argument"""
    if not os.path.isdir(path):
        msg = "Specified output directory {path!r} does not exist"
        raise argparse.ArgumentTypeError(msg)
    return path


def configure_logging():
    config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(levelname)5s - %(asctime)s] %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "clfd": {
                "level": "DEBUG",
                "handlers": ["console"],
            }
        },
    }
    logging.config.dictConfig(config)


def paths_with_duplicate_file_names(paths: Iterable[Path]) -> list[Path]:
    filename_path_mapping = defaultdict(list)
    for path in paths:
        filename_path_mapping[path.name].append(path)

    duplicates = []
    for path_list in filename_path_mapping.values():
        if len(path_list) > 1:
            duplicates.extend(path_list)

    return list(map(Path.resolve, duplicates))


def assert_psrchive_installed():
    try:
        import psrchive  # noqa: F401
    except ImportError:
        raise ImportError(
            "Could not import the PSRCHIVE Python bindings, which clfd's CLI "
            "app requires."
        ) from None


def run_program(cli_args: list[str]):
    configure_logging()
    parser = make_parser()
    args = parser.parse_args(cli_args)
    assert_psrchive_installed()

    archive_paths = set(Path(ar) for ar in args.archives)

    if args.outdir and (
        duplicates := paths_with_duplicate_file_names(archive_paths)
    ):
        msg = (
            "There are duplicate input archive file names, while 'outdir' has "
            "been specified. This is not allowed, otherwise there would be "
            "output file name collisions. Offending paths:\n"
        )
        msg += "\n".join(map(str, duplicates))
        raise ValueError(msg)

    log.info(f"Files to process: {len(archive_paths)}")

    zap_channels = load_zapfile(args.zapfile) if args.zapfile else []
    log.info(f"Ignoring {len(zap_channels)} channel indices: {zap_channels}")
    log.info(f"Using profile features: {', '.join(args.features)}")
    log.info(f"Using {args.processes} parallel processes")

    worker = Worker(
        {
            "zap_channels": zap_channels,
            "outdir": args.outdir,
            "features": args.features,
            "qmask": args.qmask,
            "despike": args.despike,
            "qspike": args.qspike,
            "save_report": not args.no_report,
        }
    )

    with multiprocessing.Pool(processes=args.processes) as pool:
        for result in pool.imap_unordered(worker, archive_paths):
            if result.output_path:
                log.info(f"Finished: {result.output_path.resolve()!s}")
            elif result.traceback:
                log.error(
                    f"Failed to process: {result.input_path.resolve()!s}\n"
                    f"{result.traceback}"
                )
        pool.close()
        pool.join()
    log.info("Done.")


def main():
    run_program(sys.argv[1:])
