from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from clfd.profile_masking import make_in_bounds_zap_indices_and_mask
from clfd.serialization import JSONSerializableDataclass


@dataclass(frozen=True)
class SpikeFindingResult(JSONSerializableDataclass):
    """
    Inputs to and result of the spike identification process.
    """

    q: float
    """
    Tukey parameter that was used for identifying bad time-phase bins.
    """

    zap_channels: list[int]
    """
    List of channel indices that were ignored in the analysis.
    """

    mask: NDArray
    """
    Binary mask with shape (num_subints, num_chans) where 'True' denotes a
    bad time-phase bin.
    """


@dataclass(frozen=True)
class SpikeSubtractionPlan:
    """
    The information necessary to replace bad data identified in the
    time-phase masking process.
    """

    valid_channels: list[int]
    """
    The complement of zapped channel indices.
    """

    mask: NDArray
    """
    Binary mask with shape (num_subints, num_chans) where 'True' denotes a
    bad time-phase bin.
    """

    replacement_values: NDArray
    """
    Replacement values with same shape as original cube.
    data[i, valid_chans, j] should be replaced by
    replacement_values[i, valid_chans, j].
    """

    def apply(self, cube: NDArray):
        """
        Apply to data cube, returning a new cube where bad values have been
        replaced.
        """
        clean_cube = cube.copy()
        for i, j in zip(*np.where(self.mask)):
            clean_cube[i, self.valid_channels, j] = self.replacement_values[
                i, self.valid_channels, j
            ]
        return clean_cube

    def subint_to_bad_phase_bins_mapping(self) -> dict[int, NDArray]:
        """
        Returns a dictionary {subint_index: bad_phase_bin_indices}.
        Useful for replacing bad data in a PSRCHIVE archive.
        """
        result = {}
        num_subints = self.mask.shape[0]
        for isub in range(num_subints):
            (bad_bins,) = np.where(self.mask[isub])
            if len(bad_bins):
                result[isub] = bad_bins
        return result


def find_time_phase_spikes(
    cube: NDArray, q: float = 4.0, zap_channels: Iterable[int] = ()
) -> tuple[SpikeFindingResult, SpikeSubtractionPlan]:
    """
    Compute a data mask based on the cube's time-phase plot (sum of the
    data along the frequency axis of the cube).

    Parameters
    ----------
    cube: NDArray
        The input data cube as a numpy array of shape
        (num_subints, num_chans, num_bins)
    q: float, optional
        Parameter that controls the min and max values that define the
        'inlier' or 'normality' range. Larger values result in fewer outliers.
    zap_channels: Iterable[int], optional
        Frequency channel indices to exclude from the outlier analysis.

    Returns
    -------
    result : SpikeFindingResult
        The results of the spike finding process, including a time-phase mask
        containing the (time, phase) bins that should be spike-subtracted.
    replacement_plan : SpikeSubtractionPlan
        The replacement plan for bad data.
    """
    num_subints, num_chans, __ = cube.shape
    zap_channels, zap_mask = make_in_bounds_zap_indices_and_mask(
        zap_channels, num_chans
    )
    if len(zap_channels) == num_chans:
        raise ValueError("Cannot run spike finding with all channels zapped")

    keep_mask = np.logical_not(zap_mask)
    (valid_channels,) = np.where(keep_mask)

    # For the purposes of this masking algorithm, we need to manipulate
    # baseline-subtracted data
    baselines = np.median(cube, axis=2).reshape(num_subints, num_chans, 1)
    subtracted_data = cube - baselines
    subints = subtracted_data[:, keep_mask, :].sum(axis=1)

    # Percentiles along time axis
    q1, med, q3 = np.percentile(subints, [25, 50, 75], axis=0)
    iqr = q3 - q1
    vmin = q1 - q * iqr
    vmax = q3 + q * iqr

    mask = (subints < vmin) | (subints > vmax)
    repvals = baselines + med / len(valid_channels)

    result = SpikeFindingResult(
        q=float(q), zap_channels=list(zap_channels), mask=mask
    )
    replacement_plan = SpikeSubtractionPlan(
        valid_channels=list(valid_channels),
        mask=mask,
        replacement_values=repvals,
    )
    return result, replacement_plan
