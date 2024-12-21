import itertools

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from numpy.typing import NDArray

from clfd import Report
from clfd.profile_masking import Stats

BANNER_BACKGROUND_COLOR = "#054a91"
BANNER_TEXT_COLOR = "w"
REJECTION_BOUNDARY_COLOR = "#e57a44"


def plot_report(report: Report) -> plt.Figure:
    """
    Plot a report, return a figure.
    """
    fig = plt.figure(figsize=(20, 10), dpi=80)

    plot_frame("Feature Values", left=0.0, right=0.5)
    corner_gridspec_kwargs = {
        "left": 0.04,
        "right": 0.49,
        "top": 0.94,
        "bottom": 0.05,
        "hspace": 0.05,
        "wspace": 0.05,
    }
    pm = report.profile_masking_result
    corner_plot(
        pm.feature_values, pm.feature_stats, pm.q, **corner_gridspec_kwargs
    )

    plot_frame("Profile Mask", left=0.5, right=0.75)
    mask_gridspec_kwargs = {
        "left": 0.54,
        "right": 0.73,
        "top": 0.94,
        "bottom": 0.05,
    }
    mask_plot(pm.mask, "subint", "channel", **mask_gridspec_kwargs)

    if report.spike_finding_result:
        plot_frame("Time-Phase Spikes", left=0.75, right=1.0)
        mask_gridspec_kwargs = {
            "left": 0.79,
            "right": 0.98,
            "top": 0.94,
            "bottom": 0.05,
        }
        mask_plot(
            report.spike_finding_result.mask,
            "subint",
            "phase bin",
            **mask_gridspec_kwargs,
        )
    return fig


def plot_frame(title: str, *, left: float, right: float):
    gs_frame = GridSpec(1, 1, top=1, bottom=0, left=left, right=right)
    axes = plt.subplot(gs_frame[0, 0])
    axes.set_facecolor("w")
    axes.tick_params(axis="both", which="both", left=False, labelleft=False)

    gs_title = GridSpec(1, 1, top=1, bottom=0.95, left=left, right=right)
    axes = plt.subplot(gs_title[0, 0])
    axes.axis("off")
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)

    rectangle = Rectangle(
        (0, 0), width=1, height=1, facecolor=BANNER_BACKGROUND_COLOR
    )
    axes.add_patch(rectangle)
    axes.text(
        0.5,
        0.5,
        title,
        fontsize=16,
        fontweight="bold",
        color=BANNER_TEXT_COLOR,
        horizontalalignment="center",
        verticalalignment="center",
    )


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
        "color": REJECTION_BOUNDARY_COLOR,
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
