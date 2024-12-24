import numpy as np
from numpy.typing import NDArray

from clfd import profile_mask2


def test_profile_masking2(data_cube: NDArray, expected_profmask: NDArray):
    result = profile_mask2(data_cube, features=("std", "ptp", "lfamp"), q=2.0, zap_channels=())
    assert np.array_equal(result.profile_mask, expected_profmask)
