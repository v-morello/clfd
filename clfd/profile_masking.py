import functools
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from clfd.features import get_feature
from clfd.serialization import JSONSerializableDataclass


@dataclass(frozen=True)
class Stats(JSONSerializableDataclass):
    """
    Stores quantiles of a profile feature.
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
class ProfileMaskingResult(JSONSerializableDataclass):
    """
    Stores inputs, intermediate results, and outputs of the profile masking
    process.
    """

    q: float
    """
    Tukey parameter that was used for deriving the mask.
    """

    zap_channels: list[int]
    """
    List of channel indices that were ignored in the analysis and then
    forcibly masked.
    """

    feature_values: dict[str, NDArray]
    """
    A dictionary where keys are feature names (e.g., `std`, `ptp`, etc.)
    and values are arrays containing the computed feature values for the data
    cube.
    """

    feature_stats: dict[str, Stats]
    """
    A dictionary where keys are feature names and values are `Stats` objects
    for the corresponding features.
    """

    mask: NDArray
    """
    A boolean array of shape (num_subints, num_chans), where `True` indicates
    bad profiles that should be masked.
    """


def make_feature_values_dict(
    cube: NDArray, features: Iterable[str]
) -> dict[str, NDArray]:
    return {name: get_feature(name)(cube) for name in features}


def make_feature_stats(feature_values: NDArray, keep_mask: NDArray) -> Stats:
    q1, med, q3 = np.percentile(feature_values[:, keep_mask], (25, 50, 75))
    return Stats(q1, med, q3)


def make_feature_stats_dict(
    feature_values_dict: dict[str, NDArray], keep_mask: NDArray
) -> dict[str, Stats]:
    return {
        name: make_feature_stats(values, keep_mask)
        for name, values in feature_values_dict.items()
    }


def make_feature_mask(
    feature_values: NDArray, feature_stats: Stats, q: float
) -> NDArray:
    vmin = feature_stats.vmin(q)
    vmax = feature_stats.vmax(q)
    return (feature_values < vmin) | (feature_values > vmax)


def make_feature_masks(
    feature_values_dict: dict[str, NDArray],
    feature_stats_dict: dict[str, NDArray],
    q: float,
) -> list[NDArray]:
    result = []
    for name in feature_values_dict:
        values = feature_values_dict[name]
        stats = feature_stats_dict[name]
        result.append(make_feature_mask(values, stats, q=q))
    return result


def make_in_bounds_zap_indices_and_mask(
    zap_channels: Iterable[int], num_chan: int
) -> tuple[NDArray, NDArray]:
    zap_channels = [i for i in zap_channels if i in range(0, num_chan)]
    zap_mask = np.zeros(num_chan, dtype=bool)
    zap_mask[zap_channels] = True
    return zap_channels, zap_mask


def profile_mask(
    cube: NDArray,
    features: Iterable[str] = ("std", "ptp", "lfamp"),
    q: float = 2.0,
    zap_channels: Iterable[int] = (),
) -> ProfileMaskingResult:
    """
    Generate a masking profile for a data cube based on statistical features.

    This function analyzes a 3D data cube along its second axis to compute
    statistical features for each profile. It then applies thresholds to these
    features to generate a mask, optionally "zapping" specific channels.

    Parameters
    ----------
    cube : NDArray
        Input data cube with shape (num_subints, num_chans, num_bins).
    features : Iterable[str], optional
        A list of profile feature names to calculate and use for masking.
    q : float, optional
        Parameter that controls the min and max values that define the 'inlier'
        or 'normality' range. For every feature, the first and third quartiles
        (Q1 and Q3) are calculated, and R = Q3 - Q1 is the interquartile range.
        The min and max acceptable values are then defined as:

        vmin = Q1 - q x R
        vmax = Q3 + q x R

        The original recommendation of Tukey is q = 1.5.
    zap_channels : Iterable[int], optional
        A list of channel indices to be ignored in the analysis and then
        forcibly masked at the end.

    Returns
    -------
    ProfileMaskingResult
    """
    num_chans = cube.shape[1]
    zap_channels, zap_mask = make_in_bounds_zap_indices_and_mask(
        zap_channels, num_chans
    )
    if len(zap_channels) == num_chans:
        raise ValueError("Cannot run profile masking with all channels zapped")

    feature_values = make_feature_values_dict(cube, features)
    feature_stats = make_feature_stats_dict(
        feature_values, np.logical_not(zap_mask)
    )

    profile_mask = functools.reduce(
        np.logical_or, make_feature_masks(feature_values, feature_stats, q)
    )
    profile_mask[:, zap_channels] = True

    return ProfileMaskingResult(
        q=float(q),
        zap_channels=sorted(zap_channels),
        feature_values=feature_values,
        feature_stats=feature_stats,
        mask=profile_mask,
    )
