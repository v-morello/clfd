import os
import itertools
import logging
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    HAS_MATPLOTLIB = True
except:
    HAS_MATPLOTLIB = False


log = logging.getLogger('clfd')


def _check_matplotlib():
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib library not available")


class CornerPlot(object):
    """ """
    def __init__(self, report):
        self.report = report
        self.num_features = len(self.report.features.columns)
        self.gridspec = None

        self._inlier_range_style = {
            'color': 'r',
            'linestyle': '--',
            'lw': 1.0
            }

    @property
    def features(self):
        return self.report.features

    @property
    def names(self):
        return list(self.features.columns)

    def _get_limits(self, name, scale_factor=3.0):
        """ Return plot limits for given feature name """
        s = self.report.stats
        q = self.report.qmask
        med = s.loc['med']
        iqr = s.loc['iqr']
        xmin = med[name] - scale_factor * (q + 1) * iqr[name]
        xmax = med[name] + scale_factor * (q + 1) * iqr[name]
        return xmin, xmax

    def _get_inlier_range(self, name):
        s = self.report.stats
        vmin = s.loc['vmin']
        vmax = s.loc['vmax']
        return vmin[name], vmax[name]

    def _define_grid(self):
        log.debug("Defining Grid")
        nf = self.num_features
        self.gridspec = GridSpec(nf, nf)
        log.debug("Defined {s:d} x {s:d} Grid for ploting".format(s=nf))

    def _scatter_plot(self, xname, yname):
        ax = plt.gca()
        x = self.features[xname]
        y = self.features[yname]
        xmin, xmax = self._get_inlier_range(xname)
        ymin, ymax = self._get_inlier_range(yname)

        ax.scatter(x, y, s=2, alpha=0.05, label=None, color='k')

        ax.plot([xmin, xmin], [ymin, ymax], **self._inlier_range_style)
        ax.plot([xmax, xmax], [ymin, ymax], **self._inlier_range_style)
        ax.plot([xmin, xmax], [ymin, ymin], **self._inlier_range_style)
        ax.plot([xmin, xmax], [ymax, ymax], **self._inlier_range_style)

        ax.set_xlim(*self._get_limits(xname))
        ax.set_ylim(*self._get_limits(yname))
        ax.grid(linestyle=':')

        ax.set_xlabel(xname, fontweight='bold')
        ax.set_ylabel(yname, fontweight='bold')
        return ax

    def _histogram(self, xname, bins=100):
        ax = plt.gca()
        x = self.features[xname]
        xmin, xmax = self._get_limits(xname)

        bins = np.linspace(xmin, xmax, bins)
        ax.hist(x, bins, histtype='step', edgecolor='#303030', lw=1)
        ax.set_xlim(xmin, xmax)
        ax.grid(linestyle=':', axis='x')

        ymin, ymax = ax.get_ylim()
        xmin, xmax = self._get_inlier_range(xname)
        ax.plot([xmin, xmin], [ymin, ymax], **self._inlier_range_style)
        ax.plot([xmax, xmax], [ymin, ymax], **self._inlier_range_style)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel(xname, fontweight='bold')
        return ax

    def plot(self, figsize=(12, 10), dpi=100):
        self._define_grid()

        f = self.report.features
        names = list(f.columns)

        fig = plt.figure(figsize=figsize, dpi=dpi)
        for ix, xname in enumerate(names):
            for iy, yname in enumerate(names):
                if ix > iy:
                    continue

                plt.subplot(self.gridspec[iy, ix])
                if xname == yname: # histogram
                    self._histogram(xname)
                else: # scatter
                    self._scatter_plot(xname, yname)

        # NOTE: if Report was not loaded from a file, fname is None
        if self.report.fname is not None:
            __, fname = os.path.split(self.report.fname)
            plt.suptitle("Corner plot: {:s}".format(fname), ha='left', x=0.39)

        plt.tight_layout()
        return fig


def profile_mask_plot(report, figsize=(12, 4), dpi=100):
    """ """
    linecolor='#303030'
    fig = plt.figure(figsize=figsize, dpi=dpi)
    gs = GridSpec(2, 2, height_ratios=(2.5, 1), width_ratios=(8, 1))

    nsub, nchan = report.profmask.shape

    ### Profile mask
    ax_mask = plt.subplot(gs[0, 0])
    # NOTE: origin set to lower. Makes life easier when plotting fraction
    # masked graphs below
    ax_mask.imshow(report.profmask, cmap='Greys', aspect='auto', origin='lower')
    ax_mask.set_ylabel("Sub-integration index")

    # NOTE: if Report was not loaded from a file, fname is None
    if report.fname is not None:
        __, fname = os.path.split(report.fname)
        ax_mask.set_title("Profile mask: {}".format(fname))
    else:
        ax_mask.set_title("Profile mask")

    ### Fraction masked in each channel
    ax_fchan = plt.subplot(gs[1, 0], sharex=ax_mask)
    fchan = report.profmask.mean(axis=0)
    ax_fchan.plot(fchan * 100.0, color=linecolor)
    ax_fchan.set_xlim(-0.5, nchan-0.5) # match imshow's xlim
    ymin, ymax = ax_fchan.get_ylim()
    ymin = max(0, ymin)
    ax_fchan.set_ylim(ymin, ymax)

    ax_fchan.set_ylabel("% masked")
    ax_fchan.set_xlabel("Channel index")
    ax_fchan.grid(linestyle=':')

    ### Fraction masked in each subint
    ax_fsub = plt.subplot(gs[0, 1], sharey=ax_mask)
    fsub = report.profmask.mean(axis=1)
    ax_fsub.plot(fsub * 100.0, range(nsub), color=linecolor)
    ax_fsub.set_ylim(-0.5, nsub - 0.5) # match imshow's xlim
    ax_fsub.set_xlabel("% masked")
    ax_fsub.grid(linestyle=':')

    plt.tight_layout()
    return fig
