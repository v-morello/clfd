import itertools
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec, SubplotSpec
from matplotlib.patches import Rectangle
from matplotlib.pyplot import Axes, Figure
from numpy.typing import NDArray

from clfd import Report
from clfd.profile_masking import Stats


@dataclass
class PlotRegion:
    left: float
    right: float
    bottom: float
    top: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def xmid(self) -> float:
        return (self.left + self.right) / 2

    @property
    def ymid(self) -> float:
        return (self.top + self.bottom) / 2

    def scaled(self, xscale: float, yscale: float) -> "PlotRegion":
        return PlotRegion(
            left=self.xmid - xscale * self.width / 2,
            right=self.xmid + xscale * self.width / 2,
            bottom=self.ymid - yscale * self.height / 2,
            top=self.ymid + yscale * self.height / 2,
        )


class Frame:
    """
    Container for a plot, delimited by a rectangle and with a title box at the
    top.
    """

    def __init__(
        self,
        title: str,
        *,
        left: float,
        right: float,
        top: float,
        bottom: float,
    ):
        self.title = title
        self.gridspec = GridSpec(
            2,
            1,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            height_ratios=(1, 24),
            hspace=0,
        )
        title_box_axes = draw_axes_with_outer_frame_only(self.gridspec[0, 0])
        draw_axes_with_outer_frame_only(self.gridspec[1, 0])
        draw_title_box_filling_axes(title_box_axes, title)

    def usable_plot_region(self) -> PlotRegion:
        g = self.gridspec
        hup, hdown = g.get_height_ratios()
        usable_height_fraction = hdown / (hdown + hup)
        return PlotRegion(
            left=g.left,
            right=g.right,
            bottom=g.bottom,
            top=g.bottom + usable_height_fraction * (g.top - g.bottom),
        )


class FrameRow(Sequence[Frame]):
    """
    Row of frames.
    """

    def __init__(
        self,
        titles: Iterable[str],
        width_ratios: Iterable[float],
    ):
        left = 0
        widths = [r / sum(width_ratios) for r in width_ratios]

        self._frames: list[Frame] = []
        for title, width in zip(titles, widths):
            frame = Frame(
                title, left=left, right=left + width, bottom=0.0, top=1.0
            )
            self._frames.append(frame)
            left += width

    def __getitem__(self, index: int) -> Frame:
        return self._frames[index]

    def __len__(self):
        return len(self._frames)


def draw_axes_with_outer_frame_only(spec: SubplotSpec) -> plt.Axes:
    axes = plt.subplot(spec)
    axes.set_facecolor("w")
    axes.tick_params(
        axis="both",
        which="both",
        bottom=False,
        top=False,
        left=False,
        right=False,
        labelleft=False,
        labelright=False,
        labeltop=False,
        labelbottom=False,
    )
    axes.set_frame_on(False)
    return axes


def draw_title_box_filling_axes(axes: Axes, title: str):
    rectangle = Rectangle(
        (0, 0),
        width=1,
        height=1,
        facecolor="#054a91",
    )
    axes.add_patch(rectangle)
    axes.text(
        0.5,
        0.5,
        title,
        fontsize=16,
        fontweight="bold",
        color="w",
        horizontalalignment="center",
        verticalalignment="center",
    )


def plot_report(report: Report) -> Figure:
    fig = plt.figure(figsize=(20, 10), dpi=80)
    feature_values_frame, profile_mask_frame, spike_mask_frame = FrameRow(
        ["Feature Values", "Profile Mask", "Time-Phase Spikes"], [9, 4, 4]
    )

    pm = report.profile_masking_result
    region = feature_values_frame.usable_plot_region().scaled(
        xscale=0.8, yscale=0.9
    )
    kwargs = {
        "left": region.left,
        "right": region.right,
        "bottom": region.bottom,
        "top": region.top,
        "wspace": 0.04,
        "hspace": 0.04,
    }
    corner_plot(pm.feature_values, pm.feature_stats, pm.q, **kwargs)

    region = profile_mask_frame.usable_plot_region().scaled(
        xscale=0.8, yscale=0.9
    )
    kwargs = {
        "left": region.left,
        "right": region.right,
        "bottom": region.bottom,
        "top": region.top,
    }
    mask_plot(pm.mask, "subint", "channel", **kwargs)

    if report.spike_finding_result is not None:
        region = spike_mask_frame.usable_plot_region().scaled(
            xscale=0.8, yscale=0.9
        )
        kwargs = {
            "left": region.left,
            "right": region.right,
            "bottom": region.bottom,
            "top": region.top,
        }
        mask_plot(
            report.spike_finding_result.mask, "subint", "phase bin", **kwargs
        )
    return fig


def corner_plot(
    feature_values: dict[str, NDArray],
    feature_stats: dict[str, Stats],
    q: float,
    **gridspec_kwargs,
):
    """
    Make a corner plot of the feature values.
    """
    rejection_boundaries_kwargs = {
        "linestyles": "--",
        "lw": 1,
        "color": "#e57a44",
    }

    num_features = len(feature_values)
    grid = GridSpec(num_features, num_features, **gridspec_kwargs)

    names = feature_values.keys()
    feature_limits = {
        name: (stats.vmin(4 * q), stats.vmax(4 * q))
        for name, stats in feature_stats.items()
    }

    for (ix, xname), (iy, yname) in itertools.combinations(
        enumerate(names), 2
    ):
        # NOTE: 'ix' increases left-right and 'iy' top-bottom
        # Scatter plots
        axes = plt.subplot(grid[iy, ix])
        xdata = feature_values[xname].ravel()
        ydata = feature_values[yname].ravel()
        axes.scatter(xdata, ydata, color="#303030", s=2, alpha=0.1)

        # Rejection boundaries
        stats_x = feature_stats[xname]
        stats_y = feature_stats[yname]
        axes.vlines(
            [stats_x.vmin(q), stats_x.vmax(q)],
            stats_y.vmin(q),
            stats_y.vmax(q),
            **rejection_boundaries_kwargs,
        )
        axes.hlines(
            [stats_y.vmin(q), stats_y.vmax(q)],
            stats_x.vmin(q),
            stats_x.vmax(q),
            **rejection_boundaries_kwargs,
        )

        # Set limits
        axes.set_xlim(*feature_limits[xname])
        axes.set_ylim(*feature_limits[yname])

        if iy == num_features - 1:
            axes.set_xlabel(xname, fontweight="bold")
        else:
            axes.set_xticklabels([])

        if ix == 0:
            axes.set_ylabel(yname, fontweight="bold")
        else:
            axes.set_yticklabels([])

    # Histograms
    num_bins = 50
    for i, name in enumerate(names):
        axes = plt.subplot(grid[i, i])
        data = feature_values[name].ravel()
        xmin, xmax = feature_limits[name]
        axes.hist(
            data,
            bins=np.linspace(xmin, xmax, num_bins),
            histtype="step",
            color="#303030",
        )

        # Rejection boundaries
        stats = feature_stats[name]
        ymin, ymax = axes.get_ylim()
        axes.vlines(
            [stats.vmin(q), stats.vmax(q)],
            ymin,
            ymax,
            **rejection_boundaries_kwargs,
        )
        axes.set_ylim(ymin, ymax)
        axes.set_yticks([])
        axes.set_yticklabels([])

        axes.set_xlim(xmin, xmax)
        if i == num_features - 1:
            axes.set_xlabel(name, fontweight="bold")
        if i != num_features - 1:
            axes.set_xticklabels([])


def mask_plot(
    mask: NDArray, dim0_name: str, dim1_name: str, **gridspec_kwargs
):
    """
    Plot a two-dimensional binary mask.
    """
    grid = GridSpec(1, 1, **gridspec_kwargs)
    dim0, dim1 = mask.shape
    xlim = (-0.5, dim0 - 0.5)
    ylim = (-0.5, dim1 - 0.5)

    axes = plt.subplot(grid[0, 0])
    axes.imshow(
        mask.T,
        aspect="auto",
        cmap="binary",
        interpolation="nearest",
        alpha=0.75,
    )
    axes.set_xlim(*xlim)
    axes.set_ylim(*ylim)
    axes.set_xlabel(f"{dim0_name.capitalize()} index", fontweight="bold")
    axes.set_ylabel(f"{dim1_name.capitalize()} index", fontweight="bold")
