from typing import Callable, Iterable

import numpy as np
import pytest
from numpy.typing import NDArray

from clfd import profile_mask
from clfd.features import available_features
from clfd.serialization import json_dumps, json_loads

from .utils import ndarray_eq


@pytest.mark.parametrize(
    "feature",
    available_features().values(),
    ids=available_features().keys(),
)
def test_feature_returns_ndarray_with_expected_shape(
    data_cube: NDArray, feature: Callable
):
    result = feature(data_cube)
    assert isinstance(result, np.ndarray)
    assert result.shape == data_cube.shape[:2]


def test_profile_masking(data_cube: NDArray, expected_profmask: NDArray):
    result = profile_mask(
        data_cube, features=("std", "ptp", "lfamp"), q=2.0, zap_channels=()
    )
    assert np.array_equal(result.mask, expected_profmask)


@pytest.mark.parametrize(
    "zap_channels", [[0], [127], [17, 3, 93, 42], range(42, 93)], ids=repr
)
def test_profile_masking_with_zapped_channels(
    data_cube: NDArray, zap_channels: Iterable[int]
):
    result = profile_mask(data_cube, q=1.0e9, zap_channels=zap_channels)
    assert set(result.zap_channels) == set(zap_channels)
    assert result.zap_channels == sorted(result.zap_channels)
    assert np.all(result.mask[:, zap_channels])


def test_profile_masking_ignores_out_of_range_zap_channels(data_cube: NDArray):
    result = profile_mask(data_cube, q=1.0e9, zap_channels=range(120, 140))

    expected_zap_chanels = list(range(120, 128))
    assert result.zap_channels == expected_zap_chanels

    is_whole_channel_masked = np.ufunc.reduce(
        np.logical_and, result.mask, axis=1
    )
    assert np.all(is_whole_channel_masked[120:128])
    assert np.all(np.logical_not(is_whole_channel_masked[0:120]))


def test_profile_masking_serialization_roundtrip(data_cube: NDArray):
    result = profile_mask(
        data_cube, features=("std", "ptp", "lfamp"), q=2.0, zap_channels=()
    )
    serialized = json_dumps(result)
    deserialized = json_loads(serialized)
    assert ndarray_eq(deserialized, result)


def test_profile_masking_with_all_channels_zapped_raises_value_error(
    data_cube: NDArray,
):
    num_chan = data_cube.shape[1]
    expected_msg = "Cannot run profile masking with all channels zapped"
    with pytest.raises(ValueError, match=expected_msg):
        profile_mask(data_cube, zap_channels=range(num_chan))
