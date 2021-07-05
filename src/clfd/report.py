import json
import attr
import base64
import warnings
import numpy as np
import pandas as pd  # type:ignore

from pathlib import Path
from textwrap import dedent
from typing import List, Dict, Tuple, Union, Optional


try:

    import matplotlib.pyplot as plt  # type:ignore
    from matplotlib.gridspec import GridSpec  # type:ignore

    MATPLOTLIB_WARNING = None

except:

    MATPLOTLIB_WARNING = dedent(
        """
        Note that the plotting capabilities of the Report class are now
        disabled, since matplotlib is not available. If you wish to plot 
        reports, you can install the package via pip:

        >> python -m pip install matplotlib

        Or you can (re-)install clfd with the `plots` extension:

        >> python -m pip install clfd[plots]
        """
    )


full_names = {
    "std": "Standard deviation",
    "var": "Variance",
    "ptp": "Peak-to-peak difference",
    "lfamp": "Lowest frequency bin amplitude",
    "skew": "Skew",
    "kurtosis": "Kurtosis",
    "acf": "Auto-correlation function",
}


def with_matplotlib(func):

    """
    Decorator that wraps functions which require matplotlib. In case matplotlib
    is not available or installed, we swap the function for a simple warning to
    the user.
    """

    def wrap(*args, **kwargs):

        if MATPLOTLIB_WARNING is None:
            return func(*args, **kwargs)
        else:
            return warnings.warn(MATPLOTLIB_WARNING)

    return wrap


class CustomJSONEncoder(json.JSONEncoder):

    """
    Add additional serialisation capabilities to the traditional `JSONEncoder`
    from the `json` module in the Python standard library for `ndarray`s from
    `numpy` and `DataFrames` from `pandas`. We will use this to serialise and
    deserialise `Report` objects.
    """

    def default(self, obj):

        """"""

        if isinstance(obj, np.ndarray):
            b64_bytes = base64.b64encode(np.ascontiguousarray(obj).data)
            b64_str = b64_bytes.decode()
            return dict(
                data=b64_str,
                fmt="ndarray",
                shape=obj.shape,
                dtype=str(obj.dtype),
            )

        if isinstance(obj, pd.DataFrame):
            return dict(
                data=json.loads(
                    obj.to_json(
                        orient="table",
                        double_precision=15,
                    )
                ),
                fmt="DataFrame",
            )

        return super(CustomJSONEncoder, self).default(obj)


def custom_object_hook(items: Dict):

    """
    Defining a custom object hook that will decode `ndarray`s and `DataFrame`s
    serialised by our `CustomJSONEncoder`.
    """

    fmt = items.get("fmt", None)

    if fmt == "ndarray":
        b64_bytes = items["data"].encode()
        data = base64.b64decode(b64_bytes)
        return np.frombuffer(
            data,
            items["dtype"],
        ).reshape(items["shape"])

    if fmt == "DataFrame":
        return pd.read_json(
            json.dumps(items["data"]),
            orient="table",
        )

    return items


@attr.s(repr=False, auto_attribs=True)
class Report(object):

    """"""

    Q: float
    feats: pd.DataFrame
    stats: pd.DataFrame
    profile_mask: np.ndarray

    Q_spike: Optional[float] = None
    time_phz_mask: Optional[np.ndarray] = None
    zapchans: Optional[Union[List, np.ndarray]] = None

    version: Optional[str] = None
    filename: Optional[str] = None

    def __str__(self):
        return f"{type(self).__name__}"

    def __repr__(self):
        return str(self)

    @classmethod
    def from_dict(cls, attrs: Dict) -> "Report":

        """"""

        return cls(**attrs)

    def to_dict(self) -> Dict:

        """"""

        return attr.asdict(self)

    @classmethod
    def read_json(
        cls,
        fname: Union[str, Path],
        **kwargs,
    ) -> "Report":

        """"""

        with open(fname, "r") as fobj:
            kwargs = dict(kwargs)
            kwargs.setdefault("object_hook", custom_object_hook)
            return cls.from_dict(json.load(fp=fobj, **kwargs))

    def write_json(
        self,
        fname: Optional[Union[str, Path]],
        **kwargs,
    ) -> None:

        """"""

        if fname is None:
            if self.filename is not None:
                fname = self.filename
            else:
                raise IOError("No filename was specified. Exiting...")

        with open(fname, "w+") as fobj:
            kwargs = dict(kwargs)
            kwargs.setdefault("indent", 4)
            kwargs.setdefault("cls", CustomJSONEncoder)
            json.dump(obj=self.to_dict(), fp=fobj, **kwargs)

    @with_matplotlib
    def mask_plot(
        self,
        to_file: Optional[str] = None,
        **kwargs,
    ) -> None:

        """"""

        def plot_profile_mask(
            mask: np.ndarray,
            cmap: str,
            grid: GridSpec,
            pos: Tuple[int, int],
        ) -> plt.Axes:

            """
            Plot the profile mask.
            """

            ax = plt.subplot(grid[pos])

            ax.imshow(
                mask,
                cmap=cmap,
                aspect="auto",
                origin="lower",
            )
            ax.set_ylabel("Sub-integration index")

            if self.filename is not None:
                ax.set_title(f"Profile mask: {self.filename}")
            else:
                ax.set_title("Profile mask")

            return ax

        def plot_frac_masked_channel(
            mask: np.ndarray,
            color: str,
            grid: GridSpec,
            pos: Tuple[int, int],
        ) -> plt.Axes:

            """
            Plot the fraction masked in each channel.
            """

            frac = mask.mean(axis=0) * 100.0

            ax = plt.subplot(grid[pos])

            ax.plot(frac, color=color)

            nchan = mask.shape[1]

            # Setting x-axis limits.
            # Here we try to match the limits of the profile mask.
            ax.set_xlim(
                -0.5,
                nchan - 0.5,
            )

            # Set y-axis limits.
            ymin, ymax = ax.get_ylim()
            ymin = max(0, ymin)
            ax.set_ylim(ymin, ymax)

            ax.grid(linestyle=":")
            ax.set_ylabel("% masked")
            ax.set_xlabel("Channel index")

            return ax

        def plot_frac_masked_subint(
            mask: np.ndarray,
            color: str,
            grid: GridSpec,
            pos: Tuple[int, int],
        ) -> plt.Axes:

            """
            Plot the fraction masked in each subint.
            """

            nsub = mask.shape[0]
            fsub = mask.mean(axis=1) * 100.0

            ax = plt.subplot(grid[pos])
            ax.plot(fsub, range(nsub), color=color)

            # Setting y-axis limits.
            # Here we try to match the limits of the profile mask.
            ax.set_ylim(
                -0.5,
                nsub - 0.5,
            )

            ax.grid(linestyle=":")
            ax.set_xlabel("% masked")

        fig = plt.figure(dpi=100, figsize=(12, 4))

        grid = GridSpec(
            2,
            2,
            height_ratios=(2.5, 1),
            width_ratios=(8, 1),
        )

        color_map = "inferno"
        line_color = "#303030"

        plot_profile_mask(
            mask=self.profile_mask,
            cmap=color_map,
            grid=grid,
            pos=(0, 0),
        )

        plot_frac_masked_channel(
            mask=self.profile_mask,
            color=line_color,
            grid=grid,
            pos=(1, 0),
        )

        plot_frac_masked_subint(
            mask=self.profile_mask,
            color=line_color,
            grid=grid,
            pos=(0, 1),
        )

        plt.tight_layout()

        if to_file is None:
            fig.plot(**kwargs).show()
        else:
            fig.plot(**kwargs).savefig(to_file)
        return fig

    @with_matplotlib
    def corner(
        self,
        to_file: Optional[str] = None,
        **kwargs,
    ) -> plt.Figure:

        """"""

        Q = self.Q
        feats = self.feats
        stats = self.stats

        num_feats = len(feats.columns)

        def bounds(
            nf: str,
            Q: float,
            stats: pd.DataFrame,
            scale: float = 3.0,
        ):

            """"""

            med = stats.loc["med"][nf]
            iqr = stats.loc["iqr"][nf]
            delta = scale * (Q + 1) * iqr
            xmin = med - delta
            xmax = med + delta
            return xmin, xmax

        def inlier_range(
            nf: str,
            stats: pd.DataFrame,
        ):

            """"""

            vmin = stats.loc["vmin"][nf]
            vmax = stats.loc["vmax"][nf]
            return vmin, vmax

        def hist(x: pd.Series, nbins: int = 100):

            """"""

            ax = plt.gca()

            xmin, xmax = bounds(x.name, Q, stats)

            ax.hist(
                x,
                bins=np.linspace(xmin, xmax, nbins),
                histtype="step",
                lw=1,
                edgecolor="#303030",
            )

            ax.set_xlim(*bounds(x.name, Q, stats))
            ax.grid(linestyle=":", axis="x")

            ymin, ymax = ax.get_ylim()
            xmin, xmax = inlier_range(x.name, stats)

            for xs, ys in [
                ([xmin, xmin], [ymin, ymax]),
                ([xmax, xmax], [ymin, ymax]),
            ]:
                ax.plot(
                    xs,
                    ys,
                    lw=1.0,
                    color="r",
                    linestyle="--",
                )

            ax.set_ylim(ymin, ymax)

            ax.set_xlabel(full_names[x.name], fontweight="bold")

            return ax

        def scatter(x: pd.Series, y: pd.Series):

            """"""

            ax = plt.gca()

            xmin, xmax = inlier_range(x.name, stats)
            ymin, ymax = inlier_range(y.name, stats)

            ax.scatter(
                x,
                y,
                s=2,
                alpha=0.05,
                label=None,
                color="k",
            )

            for xs, ys in [
                ([xmin, xmin], [ymin, ymax]),
                ([xmax, xmax], [ymin, ymax]),
                ([xmin, xmax], [ymin, ymin]),
                ([xmin, xmax], [ymax, ymax]),
            ]:
                ax.plot(
                    xs,
                    ys,
                    lw=1.0,
                    color="r",
                    linestyle="--",
                )

            ax.set_xlim(*bounds(x.name, Q, stats))
            ax.set_ylim(*bounds(y.name, Q, stats))

            ax.grid(linestyle=":")

            ax.set_xlabel(full_names[x.name], fontweight="bold")
            ax.set_ylabel(full_names[y.name], fontweight="bold")

            return ax

        fig = plt.figure(dpi=100, figsize=(12, 10))
        grid = GridSpec(num_feats, num_feats)

        for ix, xname in enumerate(feats.columns):
            for iy, yname in enumerate(feats.columns):
                if ix > iy:
                    continue

                plt.subplot(grid[iy, ix])
                if xname == yname:
                    hist(feats[xname])
                else:
                    scatter(feats[xname], feats[yname])

        if self.filename is not None:
            title = f"Corner plot: {self.filename}"
        else:
            title = "Corner plot"

        plt.suptitle(
            title,
            ha="left",
            x=0.39,
        )

        plt.tight_layout()

        if to_file is None:
            fig.plot(**kwargs).show()
        else:
            fig.plot(**kwargs).savefig(to_file)
        return fig