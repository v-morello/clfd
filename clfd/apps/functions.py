import logging
import os

from clfd import ArchiveWrapper, profile_mask, time_phase_mask

log = logging.getLogger("clfd")


def load_zapfile(fname: str) -> list[int]:
    """Load zapfile into a list of channel indices."""
    log.debug(f"Loading zapfile: {fname}")
    with open(fname, "r") as file:
        zap_channels = list(map(int, file.read().strip().split()))
    return zap_channels


def cleanup_file(
    fpath,
    zap_channels,
    outdir=None,
    features=("std", "ptp", "lfamp"),
    qmask=2.0,
    despike=False,
    qspike=4.0,
    ext="clfd",
):
    # 'fpath': full-length absolute file path
    # 'fname': file name without base directory
    fpath = os.path.realpath(fpath)
    fdir, fname = os.path.split(fpath)
    basename, __ = os.path.splitext(fname)

    log.debug("Processing: {:s}".format(fpath))
    archive_wrapper = ArchiveWrapper(fpath)
    cube = archive_wrapper.data_cube()

    log.debug("{:s} data shape: {!s}".format(fname, cube.data.shape))

    # Profile masking
    result = profile_mask(cube, features, q=qmask, zap_channels=zap_channels)
    mask = result.profile_mask
    archive_wrapper.apply_profile_mask(mask)
    msg = "{:s} profiles masked: {:d} / {:d} ({:.1%})".format(
        fname, mask.sum(), mask.size, mask.sum() / float(mask.size)
    )
    log.debug(msg)

    # Spike removal (optional)
    if despike:
        tpmask, valid_chans, repvals = time_phase_mask(cube, q=qspike, zap_channels=zap_channels)
        archive_wrapper.apply_time_phase_mask(tpmask, valid_chans, repvals)
        msg = "{:s} time-phase bins masked: {:d} / {:d} ({:.1%})".format(
            fname, tpmask.sum(), tpmask.size, tpmask.sum() / float(tpmask.size)
        )
        log.debug(msg)
    else:
        # NOTE: we set those values to None to be passed as parameters to
        # the output Report
        tpmask = None
        qspike = None

    # Save output
    # outdir = None means that data products for a given input archive
    # are placed in the same directory as the archive itself
    outdir = os.path.realpath(outdir) if outdir else fdir
    outpath = "{}.{}".format(os.path.join(outdir, fname), ext)

    archive_wrapper.save(outpath)
    log.debug("Saved output archive: {:s}".format(outpath))

    # # Save report
    # if report:
    #     report_path = "{}_clfd_report.h5".format(os.path.join(outdir, basename))
    #     frequencies = archive_wrapper.channel_frequencies
    #     report = Report(
    #         features, stats, mask, qmask, frequencies, zap_channels, tpmask=tpmask, qspike=qspike
    #     )
    #     report.save(report_path)
    #     log.debug("Saved report file: {:s}".format(report_path))


class Worker:
    """
    Function-like object to be applied by a multiprocessing Pool.
    """

    def __init__(self, cleanup_file_kwargs: dict):
        self.cleanup_file_kwargs = cleanup_file_kwargs

    def __call__(self, fpath: str):
        kwargs = self.cleanup_file_kwargs | {"fpath": fpath}
        cleanup_file(**kwargs)
