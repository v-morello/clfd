import os
import logging
import multiprocessing

import clfd
import clfd.interfaces

log = logging.getLogger('clfd')


def load_zapfile(fname):
    """ Load zapfile into a list of channel indices. If 'fname' is None, return an empty list."""
    if not fname:
        log.info("No zapfile specified.")
        return []

    log.debug("Loading zapfile: {}".format(fname))
    with open(fname, "r") as fobj:
        zap_channels = list(map(int, fobj.read().strip().split()))
    log.debug("Ignoring {:d} channel indices: {!s}".format(
        len(zap_channels), zap_channels))

    return zap_channels


def cleanup_file(fpath, interface, zap_channels, features=('std', 'ptp', 'lfamp'), qmask=2.0, despike=False, qspike=2.0, ext='clfd'):
    # 'fpath': full-length absolute file path
    # 'fname': file name without base directory
    fpath = os.path.realpath(fpath)
    __, fname = os.path.split(fpath)

    log.debug("Processing: {:s}".format(fpath))

    __, extension = os.path.splitext(fpath)
    archive, cube = interface.load(fpath)

    log.debug("{:s} data shape: {!s}".format(fname, cube.data.shape))

    # Profile masking
    features = clfd.featurize(cube)
    stats, mask = clfd.profile_mask(
        features, q=qmask, zap_channels=zap_channels)
    interface.apply_profile_mask(mask, archive)
    msg = "{:s} profiles masked: {:d} / {:d} ({:.1%})".format(
        fname, mask.sum(), mask.size, mask.sum() / float(mask.size))
    log.debug(msg)

    # Spike removal (optional)
    if despike:
        tpmask, valid_chans, repvals = clfd.time_phase_mask(
            cube, q=qspike, zap_channels=zap_channels)
        interface.apply_time_phase_mask(tpmask, valid_chans, repvals, archive)
        msg = "{:s} time-phase bins masked: {:d} / {:d} ({:.1%})".format(
            fname, tpmask.sum(), tpmask.size, tpmask.sum() / float(tpmask.size))
        log.debug(msg)

    # Save output
    outpath = "{}.{}".format(fpath, ext)
    interface.save(outpath, archive)
    log.debug("Saved output archive: {:s}".format(outpath))


class CleanupWorker(object):
    """ Function-like object called by multiprocessing.Pool """

    def __init__(self, interface, zap_channels, features=('std', 'ptp', 'lfamp'), qmask=2.0, despike=False, qspike=2.0, ext='clfd'):
        self.interface = interface
        self.zap_channels = zap_channels
        self.features = features
        self.qmask = qmask
        self.despike = despike
        self.qspike = qspike
        self.ext = ext

    def __call__(self, fname):
        cleanup_file(
            fname, self.interface, self.zap_channels,
            features=self.features,
            qmask=self.qmask,
            despike=self.despike,
            qspike=self.qspike,
            ext=self.ext)


def cleanup_main(filenames, fmt='psrchive', zapfile=None, features=('std', 'ptp', 'lfamp'), qmask=2.0, despike=False, qspike=2.0, ext='clfd', processes=1):
    log.debug("Files to process: {:d}".format(len(filenames)))
    log.debug("Format: {}".format(fmt))
    interface = clfd.interfaces.get_interface(fmt)
    zap_channels = load_zapfile(zapfile)

    worker_func = CleanupWorker(interface, zap_channels, features=features,
                                qmask=qmask, despike=despike, qspike=qspike, ext=ext)

    if processes > 1:
        log.debug("Using multiprocessing with {:d} processes".format(processes))
        pool = multiprocessing.Pool(processes=processes)
        pool.map(worker_func, filenames)
        pool.close()
        pool.join()
    else:
        log.debug("Processing input files sequentially")
        for fname in filenames:
            worker_func(fname)

    log.debug("Done.")
