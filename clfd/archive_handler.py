import os
from typing import Union

import numpy as np
from numpy.typing import NDArray

from clfd.spike_finding import SpikeSubtractionPlan


class ArchiveHandler:
    """
    Simple wrapper for a psrchive.Archive object, which allows editing it.
    """

    def __init__(self, path: Union[str, os.PathLike]):
        import psrchive

        if hasattr(psrchive, "Archive_load"):
            loader = psrchive.Archive_load
        else:
            loader = psrchive.Archive.load

        self._archive = loader(str(path))

    def data_cube(self) -> NDArray:
        """
        Return the archive data as a 3-dimensional numpy array of shape
        (num_subints, num_chans, num_bins). Only Stokes I data is read.
        """
        return self._archive.get_data()[:, 0, :, :]

    def apply_profile_mask(self, mask: NDArray):
        """
        Apply profile mask to underlying archive, setting the weights of masked
        profiles to zero.
        """
        ipol = 0
        for isub, ichan in zip(*np.where(mask)):
            # NOTE: cast indices from numpy.int64 to int, otherwise
            # get_Profile() complains about argument type
            prof = self._archive.get_Profile(int(isub), ipol, int(ichan))
            prof.set_weight(0.0)

    def apply_spike_subtraction_plan(self, plan: SpikeSubtractionPlan):
        """
        Set the values of data inside bad time-phase bins to appropriate
        replacement values.
        """
        ipol = 0
        repvals = plan.replacement_values
        mapping = plan.subint_to_bad_phase_bins_mapping()

        for isub, bad_bins in mapping.items():
            for ichan in plan.valid_channels:
                # NOTE: cast indices from numpy.int64 to int, otherwise
                # get_Profile() complains about argument type
                prof = self._archive.get_Profile(isub, ipol, int(ichan))
                amps = prof.get_amps()
                amps[bad_bins] = repvals[isub, ichan, bad_bins]

    def save(self, path: Union[str, os.PathLike]):
        """
        Save archive to given path.
        """
        self._archive.unload(str(path))
