import functools
import inspect
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
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
class ProfileMasking:
    """
    TODO
    """

    feature_names: tuple[str]
    q: float
    zap_channels: tuple[int]
    feature_values: dict[str, NDArray]
    feature_stats: dict[str, Stats]
    mask: NDArray


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
) -> ProfileMasking:
    """
    TODO
    """
    zap_channels, zap_mask = make_in_bounds_zap_indices_and_mask(zap_channels, cube.shape[1])
    feature_values = make_feature_values_dict(cube, features)
    feature_stats = make_feature_stats_dict(feature_values, np.logical_not(zap_mask))
    feature_masks = make_feature_mask_dict(feature_values, feature_stats, q)

    profile_mask = functools.reduce(np.logical_or, feature_masks.values())
    profile_mask[:, zap_channels] = True

    return ProfileMasking(
        feature_names=features,
        q=q,
        zap_channels=sorted(zap_channels),
        feature_values=feature_values,
        feature_stats=feature_stats,
        mask=profile_mask,
    )
