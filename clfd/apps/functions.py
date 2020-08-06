import os
import logging
import multiprocessing

import clfd
import clfd.interfaces

log = logging.getLogger('clfd')


def load_zapfile(fname):
    """
    Load zapfile into a list of channel indices.
    If 'fname' is None, return an empty list.
    """

    if not fname:
        log.info("No zapfile specified.")
        return []

    log.debug("Loading zapfile: {}".format(fname))

    with open(fname, "r") as fobj:
        zap_channels = list(map(int,
                                fobj.read().strip().split()))

    MSG = "Ignoring {:d} channel indices: {!s}"
    log.debug(MSG.format(len(zap_channels),
                         zap_channels))

    return zap_channels


def cleanup_file(fpath,
                 interface,
                 zap_channels,
                 outdir=None,
                 features=('std', 'ptp', 'lfamp'),
                 qmask=2.0,
                 despike=False,
                 qspike=4.0,
                 ext='clfd',
                 report=True):

    # 'fpath': full-length absolute file path.
    # 'fname': file name without base directory.

    fpath = os.path.realpath(fpath)
    fdir, fname = os.path.split(fpath)
    basename, extension = os.path.splitext(fname)

    log.debug("Processing: {:s}".format(fpath))
    folded, cube = interface.load(fpath)

    log.debug("{:s} data shape: {!s}".format(fname, cube.data.shape))

    # Profile masking.

    features = clfd.featurize(cube,
                              features=features)

    stats, mask = clfd.profile_mask(features,
                                    q=qmask,
                                    zap_channels=zap_channels)
    interface.apply_profile_mask(mask, folded)

    msg = "{:s} profiles masked: {:d} / {:d} ({:.1%})"
    msg = msg.format(fname,
                     mask.sum(),
                     mask.size,
                     mask.sum() / float(mask.size))
    log.debug(msg)

    # Spike removal (optional).

    if despike:

        tpmask, valid_chans, repvals = clfd.time_phase_mask(
            cube, q=qspike, zap_channels=zap_channels)
        interface.apply_time_phase_mask(tpmask, valid_chans, repvals, folded)
        msg = "{:s} time-phase bins masked: {:d} / {:d} ({:.1%})".format(
            fname, tpmask.sum(), tpmask.size, tpmask.sum() / float(tpmask.size))
        log.debug(msg)

    else:

        # NOTE: We set those values to `None` to be passed
        # as parameters to the output `Report`.

        tpmask = None
        qspike = None

    # Save output

    if outdir is None:
        outdir = fdir

    outpath = "{}.{}".format(os.path.join(outdir, fname), ext)

    interface.save(outpath, folded)
    log.debug("Saved output folded: {:s}".format(outpath))

    # Save report

    if report:
        report_path   = os.path.join(outdir, basename)
        report_path = "{}_clfd_report.h5".format(report_path)

        frequencies = interface.get_frequencies(folded)

        report = clfd.Report(features,
                             stats,
                             mask,
                             qmask,
                             frequencies,
                             zap_channels,
                             tpmask=tpmask,
                             qspike=qspike)

        report.save(report_path)
        log.debug("Saved report file: {:s}".format(report_path))


class CleanupWorker(object):

    """
    Function-like object called by multiprocessing.Pool.
    """

    def __init__(self,
                 interface,
                 zap_channels,
                 outdir=None,
                 features=('std', 'ptp', 'lfamp'),
                 qmask=2.0,
                 despike=False,
                 qspike=4.0,
                 ext='clfd',
                 report=True):

        self.interface = interface
        self.zap_channels = zap_channels
        self.outdir = outdir
        self.features = features
        self.qmask = qmask
        self.despike = despike
        self.qspike = qspike
        self.ext = ext
        self.report = report

    def __call__(self, fname):

        cleanup_file(
            fname, self.interface, self.zap_channels,
            outdir=self.outdir,
            features=self.features,
            qmask=self.qmask,
            despike=self.despike,
            qspike=self.qspike,
            ext=self.ext,
            report=self.report)


def cleanup_main(filenames,
                 fmt='psrchive',
                 outdir=None,
                 zapfile=None,
                 features=('std', 'ptp', 'lfamp'),
                 qmask=2.0,
                 despike=False,
                 qspike=4.0,
                 ext='clfd',
                 report=True,
                 processes=1):

    log.debug("Files to process: {:d}".format(len(filenames)))
    log.debug("Format: {}".format(fmt))

    interface = clfd.interfaces.get_interface(fmt)
    zap_channels = load_zapfile(zapfile)

    # if outdir is `None`, it means that data products for
    # each input file are placed in the same directory as
    # that file.

    if outdir is not None:
        outdir = os.path.realpath(outdir)

    worker_func = CleanupWorker(interface,
                                zap_channels,
                                outdir=outdir,
                                features=features,
                                qmask=qmask,
                                despike=despike,
                                qspike=qspike,
                                ext=ext,
                                report=report)

    if processes > 1:
        msg = "Using multiprocessing with {:d} processes"
        log.debug(msg.format(processes))
        pool = multiprocessing.Pool(processes=processes)
        pool.map(worker_func, filenames)
        pool.close()
        pool.join()
    else:
        log.debug("Processing input files sequentially")
        for fname in filenames:
            worker_func(fname)

    log.debug("Done.")
