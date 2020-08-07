import unittest
import os
import tempfile

import numpy
from clfd import DataCube, profile_mask, featurize, time_phase_mask
from clfd.interfaces import PfdInterface

from utils import get_example_data_path

try:
    from ptypes.presto import PTypePFD
    HAS_PTYPES = True
except ImportError:
    HAS_PTYPES = False

class TestPfdProcessing(unittest.TestCase):

    """
    Test PFD interface.
    """

    def setUp(self):
        self.pfd_data_fname = os.path.join(get_example_data_path(),
                                           "pfd_example.pfd")
        self.nchan = 4096

        self.foff = 0.048828
        self.fch1 = 300.024926
        self.frequencies = self.fch1 + self.foff * numpy.arange(self.nchan)

    @unittest.skipUnless(HAS_PTYPES, "")
    def test_get_frequencies(self):

        """
        Check that the get_frequencies() method works as expected.
        """

        pfd, cube = PfdInterface.load(self.pfd_data_fname)
        freqs = PfdInterface.get_frequencies(pfd)
        self.assertTrue(numpy.allclose(freqs, self.frequencies))

    @unittest.skipUnless(HAS_PTYPES, "")
    def test_load_save_pfd(self):

        pfd, cube = PfdInterface.load(self.pfd_data_fname)

        with tempfile.NamedTemporaryFile(mode="wb",
                                         suffix='.pfd',
                                         delete=False) as fobj:
            fname = fobj.name
        PfdInterface.save(fname, pfd)

        pfd2, cube2 = PfdInterface.load(fname)

        self.assertTrue(numpy.allclose(cube.orig_data,
                                       cube2.orig_data))
        os.remove(fname)

    @unittest.skipUnless(HAS_PTYPES, "")
    def test_profile_masking(self):

        pfd, cube = PfdInterface.load(self.pfd_data_fname)
        features = featurize(cube, features=["std", "ptp", "lfamp"])
        stats, mask = profile_mask(features, q=2.0, zap_channels=range(10))
        PfdInterface.apply_profile_mask(mask, pfd)
        self.assertEqual(mask.shape, (cube.num_subints, cube.num_chans))

    @unittest.skipUnless(HAS_PTYPES, "")
    def test_time_phase_masking(self):

        """
        Test the application of the mask only.
        The time_phase_mask() function has its
        own unit tests elsewhere.
        """

        pfd, cube = PfdInterface.load(self.pfd_data_fname)
        q = 2.0
        zap_channels = range(10)

        mask, valid_chans, repvals = time_phase_mask(cube, q=q, zap_channels=zap_channels)
        PfdInterface.apply_time_phase_mask(mask, valid_chans, repvals, pfd)

        ##### Check replacement of values behaves as expected. #####
        # Once bad values have been replaced, if we call time_phase_mask() again
        # with the same params, then no previously flagged time-phase bins should
        # be flagged again.
        # NOTE: HOWEVER, new bins can still get flagged !
        # That is because once the old outliers have been replaced by "good"
        # values, the range of acceptable value is reduced which may push
        # previously "normal" points into outlier status.

        clean_cube = DataCube.from_pfd(pfd)
        newmask, __, __ = time_phase_mask(clean_cube, q=q, zap_channels=zap_channels)

        # Check that no bin is flagged in both masks

        self.assertFalse(numpy.any(mask & newmask))


if __name__ == "__main__":
    unittest.main()
