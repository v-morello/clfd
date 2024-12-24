from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from clfd.profile_masking import make_in_bounds_zap_indices_and_mask


@dataclass(frozen=True)
class TimePhaseMasking:
    """
    TODO
    """

    q: float
    zap_channels: tuple[int]
    mask: NDArray


def time_phase_mask(cube: NDArray, q: float = 4.0, zap_channels: Iterable[int] = ()):
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
    zap_channels, zap_mask = make_in_bounds_zap_indices_and_mask(zap_channels, num_chans)
    keep_mask = np.logical_not(zap_mask)
    (valid_chans,) = np.where(keep_mask)

    # For the purposes of this masking algorithm, we need to manipulate
    # baseline-subtracted data
    baselines = np.median(cube, axis=2).reshape(num_subints, num_chans, 1)
    subtracted_data = cube - baselines
    subints = subtracted_data[:, keep_mask, :].sum(axis=1)

    # Q1, median, Q3 along time axis
    q1, med, q3 = np.percentile(subints, [25, 50, 75], axis=0)
    iqr = q3 - q1
    vmin = q1 - q * iqr
    vmax = q3 + q * iqr

    mask = (subints < vmin) | (subints > vmax)
    repvals = baselines + med / len(valid_chans)
    return mask, valid_chans, repvals
