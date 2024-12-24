import numpy as np
from numpy.typing import NDArray

from clfd import time_phase_mask


def test_time_phase_masking_produces_expected_mask(data_cube: NDArray, expected_tpmask: NDArray):
    result = time_phase_mask(data_cube, q=2.0, zap_channels=())
    num_subints, __, num_bins = data_cube.shape
    assert result.mask.shape == (num_subints, num_bins)
    assert result.replacement_values.shape == data_cube.shape
    assert np.array_equal(result.mask, expected_tpmask)


def test_time_phase_masking_produces_expected_valid_channels(data_cube: NDArray):
    zap_channels = range(10, 42)
    result = time_phase_mask(data_cube, zap_channels=zap_channels)

    num_chans = data_cube.shape[1]
    assert not set(result.valid_channels).intersection(zap_channels)
    assert set(result.valid_channels).union(set(zap_channels)) == set(range(num_chans))


def test_data_replaced_after_time_phase_masking_does_not_get_flagged_again(data_cube: NDArray):
    """
    Once bad values have been replaced, if we call time_phase_mask() again
    **with the same params**, then no previously flagged time-phase bins should
    be flagged again (NOTE: new time-phase bins may get flagged though)
    """
    q = 2.0
    zap_channels = range(10, 42)
    result = time_phase_mask(data_cube, q=q, zap_channels=zap_channels)
    clean_cube = result.apply(data_cube)
    new_result = time_phase_mask(clean_cube, q=q, zap_channels=zap_channels)
    assert not np.any(new_result.mask & result.mask)
