import argparse
import logging
import json
import os

import clfd
import clfd.interfaces

log = logging.getLogger("clfd.cleanup")

def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--format",
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
        default=2.0,
        help="Tukey's rule parameter for the zero DM spike removal algorithm.",
    )
    parser.add_argument(
        "-e",
        "--ext",
        type=str,
        default="clfd",
        help="Extension given to the clean output files.",
    )
    parser.add_argument("files", type=str, nargs="+", help="Input file(s)")
    args = parser.parse_args()
    return args


def load_zapfile(fname):
    """ Load zapfile into a list of channel indices. """
    with open(fname, "r") as fobj:
        zap_channels = list(map(int, fobj.read().strip().split()))
    return zap_channels

def main(args):
    interface = clfd.interfaces.get_interface(args.format)
    log.info("Using feature names: {!s}".format(args.features))

    if args.zapfile:
        zap_channels = load_zapfile(args.zapfile)
    else:
        zap_channels = []
    log.info("Number of user-defined zapped channels: {:d}".format(len(zap_channels)))
    log.info("Number of files to process: {:d} \n".format(len(args.files)))

    for fname in args.files:
        log.info("Processing archive: {:s}".format(fname))
        basename, extension = fname.rsplit('.', 1)
        archive, cube = interface.load(fname)
        
        log.info("Data shape: {!s}".format(cube.data.shape))

        ### Profile masking
        features = clfd.featurize(cube)
        stats, mask = clfd.profile_mask(features, q=args.qmask, zap_channels=zap_channels)

        interface.apply_profile_mask(mask, archive)
        num_profiles = mask.size
        num_profiles_masked = mask.sum()

        report = {
            "input_file": os.path.realpath(fname),
            "features": args.features,
            "qmask" : args.qmask,
            "zapped_channels": zap_channels,
            "num_subints" : cube.num_subints,
            "num_channels" : cube.num_chans,
            "num_bins" : cube.num_bins,
            "num_profiles" : mask.size,
            "num_profiles_masked" : mask.sum(),
            "despike" : args.despike
            }

        ### Spike removal (optional)
        if args.despike:
            log.info("Applying zero DM spike removal algorithm")
            tpmask, valid_chans, repvals = clfd.time_phase_mask(cube, q=args.qspike, zap_channels=zap_channels)
            interface.apply_time_phase_mask(tpmask, valid_chans, repvals, archive)
            report.update({
                "num_time_phase_bins" : tpmask.size,
                "num_time_phase_bins_masked": tpmask.sum()
                })
        
        outname = "{}.{}".format(fname, args.ext)
        interface.save(outname, archive)
        log.info("Saved output archive: {:s} \n".format(outname))

        report_fname = "{}.clfd_report.json".format(basename)
        with open(report_fname, "w") as fobj:
            text = json.dumps(report, indent=4) + "\n"
            fobj.write(text)

if __name__ == "__main__":
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())

    args = parse_arguments()
    main(args)
