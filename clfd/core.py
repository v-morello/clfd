import functools
import inspect
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
import pandas
from numpy.typing import NDArray

import clfd.features as pf

AVAILABLE_FEATURES: dict[str, Callable] = dict(inspect.getmembers(pf, inspect.isfunction))


@dataclass(frozen=True)
class Stats:
    """
    TODO
    """

    q1: float
    med: float
    q3: float

    @property
    def iqr(self) -> float:
        return self.q3 - self.q1

    def vmin(self, q: float) -> float:
        return self.q1 - q * self.iqr

    def vmax(self, q: float) -> float:
        return self.q3 + q * self.iqr


@dataclass(frozen=True)
class MaskingResult:
    """
    TODO
    """

    feature_names: tuple[str]
    q: float
    zap_channels: tuple[int]
    feature_values: dict[str, NDArray]
    feature_stats: dict[str, Stats]
    profile_mask: NDArray


def make_feature_values_dict(cube: NDArray, features: Iterable[str]) -> dict[str, NDArray]:
    invalid_names = set(features).difference(set(AVAILABLE_FEATURES.keys()))
    if invalid_names:
        raise ValueError(f"Invalid feature names: {invalid_names}")
    return {name: getattr(pf, name)(cube) for name in features}


def make_feature_stats(feature_values: NDArray, keep_mask: NDArray) -> Stats:
    q1, med, q3 = np.percentile(feature_values[:, keep_mask], (25, 50, 75))
    return Stats(q1, med, q3)


def make_feature_stats_dict(
    feature_values_dict: dict[str, NDArray], keep_mask: NDArray
) -> dict[str, Stats]:
    return {
        name: make_feature_stats(values, keep_mask) for name, values in feature_values_dict.items()
    }


def make_feature_mask(feature_values: NDArray, feature_stats: Stats, q: float) -> NDArray:
    vmin = feature_stats.vmin(q)
    vmax = feature_stats.vmax(q)
    return (feature_values < vmin) | (feature_values > vmax)


def make_feature_mask_dict(
    feature_values_dict: dict[str, NDArray], feature_stats_dict: dict[str, NDArray], q: float
) -> dict[str, NDArray]:
    result = {}
    for name in feature_values_dict:
        values = feature_values_dict[name]
        stats = feature_stats_dict[name]
        result[name] = make_feature_mask(values, stats, q=q)
    return result


def profile_mask(
    cube: NDArray,
    features: Iterable[str] = ("std", "ptp", "lfamp"),
    q: float = 2.0,
    zap_channels: Iterable[int] = (),
) -> MaskingResult:
    """
    TODO
    """
    num_chan = cube.shape[1]
    zap_channels = [i for i in zap_channels if i in range(0, num_chan)]
    zap_mask = np.zeros(num_chan, dtype=bool)
    zap_mask[zap_channels] = True

    feature_values = make_feature_values_dict(cube, features)
    feature_stats = make_feature_stats_dict(feature_values, np.logical_not(zap_mask))
    feature_masks = make_feature_mask_dict(feature_values, feature_stats, q)

    profile_mask = functools.reduce(np.logical_or, feature_masks.values())
    profile_mask[:, zap_channels] = True

    return MaskingResult(
        feature_names=features,
        q=q,
        zap_channels=sorted(zap_channels),
        feature_values=feature_values,
        feature_stats=feature_stats,
        profile_mask=profile_mask,
    )


def time_phase_mask(cube: NDArray, q: float = 4.0, zap_channels: list[int] = []):
    """Compute a data mask based on the cube's time-phase plot (sum of the
    data along the frequency axis of the cube).

    Parameters
    ----------
    cube: NDArray
        The input data cube as a numpy array of shape
        (num_subints, num_chans, num_bins)
    q: float, optional (default: 4.0)
        Parameter that controls the min and max values that define the 'inlier' or
        'normality' range.
    zap_channels: list or array of ints, optional (default: [])
        Frequency channel indices to exclude from the outlier analysis.

    Returns
    -------
    mask: ndarray
        A two dimensional boolean numpy array, with shape (num_subints, num_bins).
        A value of True means that the associated time-phase bin is an outlier.
    valid_chans: ndarray
        List of channel indices that are not part of 'zap_channels'. In these
        valid channels, bad data values are allowed to be replaced.
    repvals: ndarray
        Three dimensional array with same shape as the input data cube, containing
        the appropriate replacement values for bad data points in the original archive.
        A bad time-phase bin with indices (i, j) means that
        orig_data[i, valid_chans, j] should be replaced by repvals[i, valid_chans, j].
    """
    num_subints, num_chans, __ = cube.shape
    valid_chans_mask = np.ones(num_chans, dtype=bool)
    if zap_channels:
        valid_chans_mask[zap_channels] = False
    num_valid_chans = valid_chans_mask.sum()
    valid_chans = np.where(valid_chans_mask)[0]

    # For the purposes of this masking algorithm, we need to manipulate
    # baseline-subtracted data
    baselines = np.median(cube, axis=2).reshape(num_subints, num_chans, 1)
    subtracted_data = cube - baselines

    subints = subtracted_data[:, valid_chans, :].sum(axis=1)
    pcts = np.percentile(subints, [25, 50, 75], axis=0)  # Q1, median, Q3 along time axis
    stats = pandas.DataFrame(pcts).rename({0: "q1", 1: "med", 2: "q3"})
    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - q * stats.loc["iqr"]
    stats.loc["vmax"] = stats.loc["q3"] + q * stats.loc["iqr"]

    mask = (subints < stats.loc["vmin"].values) | (subints > stats.loc["vmax"].values)

    repvals = baselines + stats.loc["med"].values / num_valid_chans
    return mask, valid_chans, repvals
