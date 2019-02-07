import numpy as np
from clfd import DataCube

try:
    import psrchive
except:
    pass


class Interface(object):
    """ Base class for an interface to some file format. """
    @staticmethod
    def get_frequencies(archive):
        """ Return channel frequencies in MHz, as a numpy array"""
        raise NotImplementedError

    @staticmethod
    def apply_profile_mask(mask, archive):
        raise NotImplementedError

    @staticmethod
    def apply_time_phase_mask(mask, valid_chans, repvals, archive):
        raise NotImplementedError

    @staticmethod
    def load(fname):
        raise NotImplementedError

    @staticmethod
    def save(fname, archive):
        raise NotImplementedError


class PsrchiveInterface(Interface):
    """ Interface to PSRCHIVE format. """
    @staticmethod
    def apply_profile_mask(mask, archive):
        """ Apply profile mask to folded archive produced with PSRCHIVE, setting
        the weights of masked profiles to zero.

        Parameters
        ----------
        mask: ndarray
            The boolean mask obtained with the profile_mask() function.
        archive: psrchive.Archive
            The Archive object to which the mask will be applied.
        """
        ipol = 0
        for isub, ichan in np.vstack(np.where(mask)).T:
            archive.get_Profile(isub, ipol, ichan).set_weight(0.0)

    @staticmethod
    def apply_time_phase_mask(mask, valid_chans, repvals, archive):
        """ Apply time-phase mask to folded archive produced with PSRCHIVE, setting
        the values of bad time-phase bins along the frequency dimension to appropriate
        replacement values. All arguments except the last are the output of the
        time_phase_mask() function.
        """
        ipol = 0

        # Replacement dictionary
        # {subint_index: [bad_phase_bins]}
        repdict = {}
        num_subints, num_bins = mask.shape
        for isub in range(num_subints):
            bad_bins = np.where(mask[isub])[0]
            if len(bad_bins):
                repdict[isub] = bad_bins
        
        for isub, bad_bins in repdict.items():
            for ichan in valid_chans:
                amps = archive.get_Profile(isub, ipol, ichan).get_amps()
                amps[bad_bins] = repvals[isub, ichan, bad_bins]

    @staticmethod
    def get_frequencies(archive):
        return archive.get_frequencies()

    @staticmethod
    def load(fname):
        archive = psrchive.Archive_load(fname)
        return archive, DataCube.from_psrchive(archive)

    @staticmethod
    def save(fname, archive):
        archive.unload(fname)


def get_interface(fmt):
    """ Get Interface class for given format name. """
    interfaces = {"psrchive": PsrchiveInterface}
    fmt = fmt.lower()
    if not fmt in interfaces:
        msg = "No interface for format: {:s}".format(fmt)
        raise ValueError(msg)
    return interfaces[fmt]
