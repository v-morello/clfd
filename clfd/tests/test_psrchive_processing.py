import unittest
import os
import tempfile

import numpy
from clfd import DataCube, profile_mask, featurize, time_phase_mask
from clfd.interfaces import PsrchiveInterface

from utils import get_example_data_path

try:
    import psrchive
    HAS_PSRCHIVE = True
except ImportError:
    HAS_PSRCHIVE = False


class TestPsrchiveProcessing(unittest.TestCase):
    """ Test PSRCHIVE interface. """
    def setUp(self):
        self.psrchive_data_fname = os.path.join(get_example_data_path(), "psrchive_example.ar")
        self.nchan = 128
        # frequency offset (i.e. channel width), negative because the first 
        # channel has the highest frequency
        self.foff = -3.125
        self.fch1 = 1580.43701172
        self.frequencies = self.fch1 + self.foff * numpy.arange(self.nchan)

    @unittest.skipUnless(HAS_PSRCHIVE, "")
    def test_get_frequencies(self):
        """ Check that the get_frequencies() method works as expected """
        archive, cube = PsrchiveInterface.load(self.psrchive_data_fname)
        freqs = PsrchiveInterface.get_frequencies(archive)
        self.assertTrue(numpy.allclose(freqs, self.frequencies))

    @unittest.skipUnless(HAS_PSRCHIVE, "")
    def test_load_save_psrchive(self):
        archive, cube = PsrchiveInterface.load(self.psrchive_data_fname)

        with tempfile.NamedTemporaryFile(mode="wb", suffix='.ar', delete=False) as fobj:
            fname = fobj.name
        PsrchiveInterface.save(fname, archive)

        archive2, cube2 = PsrchiveInterface.load(fname)

        # In PSRFITS the data are stored as 16-bit integers
        # with a separate offset and scale parameter for each profile
        # Hence the higher than default tolerance
        self.assertTrue(numpy.allclose(cube.orig_data, cube2.orig_data, atol=1e-6))
        os.remove(fname)

    @unittest.skipUnless(HAS_PSRCHIVE, "")
    def test_profile_masking(self):
        archive, cube = PsrchiveInterface.load(self.psrchive_data_fname)
        features = featurize(cube, features=["std", "ptp", "lfamp"])
        stats, mask = profile_mask(features, q=2.0, zap_channels=range(10))
        PsrchiveInterface.apply_profile_mask(mask, archive)
        self.assertEqual(mask.shape, (cube.num_subints, cube.num_chans))

    @unittest.skipUnless(HAS_PSRCHIVE, "")
    def test_time_phase_masking(self):
        """ Test the application of the mask only. The time_phase_mask() function
        has its own unit tests elsewhere. """
        archive, cube = PsrchiveInterface.load(self.psrchive_data_fname)
        q = 2.0
        zap_channels = range(10)

        mask, valid_chans, repvals = time_phase_mask(cube, q=q, zap_channels=zap_channels)
        PsrchiveInterface.apply_time_phase_mask(mask, valid_chans, repvals, archive)

        ##### Check replacement of values behaves as expected #####
        # Once bad values have been replaced, if we call time_phase_mask() again
        # with the same params, then no previously flagged time-phase bins should be
        # flagged again.
        # NOTE: HOWEVER, new bins can still get flagged !
        # That is because once the old outliers have been replaced by "good" values, 
        # the range of acceptable value is reduced which may push previously "normal" points 
        # into outlier status.
        clean_cube = DataCube.from_psrchive(archive)
        newmask, __, __ = time_phase_mask(clean_cube, q=q, zap_channels=zap_channels)

        # Check that no bin is flagged in both masks
        self.assertFalse(numpy.any(mask & newmask))


if __name__ == "__main__":
    unittest.main()
