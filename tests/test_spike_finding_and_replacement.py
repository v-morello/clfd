import numpy as np
import pytest
from numpy.typing import NDArray

from clfd import find_time_phase_spikes


def test_find_time_phase_spikes_produces_expected_mask(
    data_cube: NDArray, expected_tpmask: NDArray
):
    result, __ = find_time_phase_spikes(data_cube, q=2.0, zap_channels=())
    num_subints, __, num_bins = data_cube.shape
    assert result.mask.shape == (num_subints, num_bins)
    assert np.array_equal(result.mask, expected_tpmask)


def test_find_time_phase_spikes_produces_expected_valid_channels(
    data_cube: NDArray,
):
    zap_channels = range(10, 42)
    __, plan = find_time_phase_spikes(data_cube, zap_channels=zap_channels)

    num_chans = data_cube.shape[1]
    assert not set(plan.valid_channels).intersection(zap_channels)
    assert set(plan.valid_channels).union(set(zap_channels)) == set(
        range(num_chans)
    )


def test_replaced_spike_data_does_not_get_flagged_again(
    data_cube: NDArray,
):
    """
    Once bad values have been replaced, if we call time_phase_mask() again
    **with the same params**, then no previously flagged time-phase bins should
    be flagged again (NOTE: new time-phase bins may get flagged though)
    """
    q = 2.0
    zap_channels = range(10, 42)
    result, plan = find_time_phase_spikes(
        data_cube, q=q, zap_channels=zap_channels
    )
    clean_cube = plan.apply(data_cube)
    new_result, __ = find_time_phase_spikes(
        clean_cube, q=q, zap_channels=zap_channels
    )
    assert not np.any(new_result.mask & result.mask)


def test_find_time_phase_spikes_with_all_channels_zapped_raises_value_error(
    data_cube: NDArray,
):
    num_chan = data_cube.shape[1]
    expected_msg = "Cannot run spike finding with all channels zapped"
    with pytest.raises(ValueError, match=expected_msg):
        find_time_phase_spikes(data_cube, zap_channels=range(num_chan))
