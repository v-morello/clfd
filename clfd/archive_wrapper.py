import os
from typing import Iterable, Union

import numpy as np
from numpy.typing import NDArray


class ArchiveWrapper:
    """
    Simple wrapper for a psrchive.Archive object, which allows editing it.
    """

    def __init__(self, path: Union[str, os.PathLike]):
        import psrchive

        try:
            archive = psrchive.Archive_load(str(path))
        except AttributeError:
            archive = psrchive.Archive.load(str(path))

        self._archive = archive

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

        Parameters
        ----------
        mask: ndarray
            The boolean mask obtained with the profile_mask() function.
        """
        ipol = 0
        for isub, ichan in np.vstack(np.where(mask)).T:
            # NOTE: cast indices from numpy.int64 to int, otherwise
            # get_Profile() complains about argument type
            self._archive.get_Profile(int(isub), ipol, int(ichan)).set_weight(0.0)

    def apply_time_phase_mask(self, mask: NDArray, valid_chans: Iterable[int], repvals: NDArray):
        """
        Apply time-phase mask to underlying archive, setting the values of bad
        time-phase bins to appropriate replacement values. All arguments are
        the output of the time_phase_mask() function.
        """
        ipol = 0

        # Replacement dictionary
        # {subint_index: [bad_phase_bins]}
        repdict = {}
        num_subints, __ = mask.shape
        for isub in range(num_subints):
            bad_bins = np.where(mask[isub])[0]
            if len(bad_bins):
                repdict[isub] = bad_bins

        for isub, bad_bins in repdict.items():
            for ichan in valid_chans:
                # NOTE: cast indices from numpy.int64 to int, otherwise
                # get_Profile() complains about argument type
                amps = self._archive.get_Profile(int(isub), ipol, int(ichan)).get_amps()
                amps[bad_bins] = repvals[isub, ichan, bad_bins]

    @property
    def channel_frequencies(self) -> NDArray:
        """
        Channel frequencies in Hz, as a numpy array.
        """
        n = self._archive.get_nchan()
        # bw can be negative, which means that the first channel is the one
        # with the top frequency
        bw = self._archive.get_bandwidth()
        cw = bw / n
        fc = self._archive.get_centre_frequency()

        # Centre frequencies of first and last channel
        fch1 = fc - (bw - cw) / 2.0
        fchn = fc + (bw - cw) / 2.0
        return np.linspace(fch1, fchn, n)

    def save(self, path: Union[str, os.PathLike]):
        self._archive.unload(str(path))
