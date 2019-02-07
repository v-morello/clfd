import unittest
import os
import inspect
import tempfile
import numpy
import clfd
import clfd.features

from utils import get_example_data_path

def load_test_datacube():
    fname = os.path.join(get_example_data_path(), "npy_example.npy")
    return clfd.DataCube.from_npy(fname)

def apply_time_phase_mask(mask, valid_chans, repvals, orig_data):
    """ Apply time-phase mask to original input data (BEFORE baseline subtraction). 
    If (i, j) is a True element of the mask, then replace 
    orig_data[i, valid_chans, j] by repvals[i, valid_chans, j].
    
    Returns a copy of orig_data with bad values replaced.
    """
    clean_data = orig_data.copy()
    for i, j in zip(*numpy.where(mask)):
        clean_data[i, valid_chans, j] = repvals[i, valid_chans, j]
    return clean_data


class TestTimePhaseMask(unittest.TestCase):
    def setUp(self):
        self.cube = load_test_datacube()

    def test_time_phase_mask(self):
        q = 2.0
        zap_channels = range(10)
        all_channels = range(self.cube.num_chans)
        
        mask, valid_chans, repvals = clfd.time_phase_mask(self.cube, q=q, zap_channels=zap_channels)

        # Check that valid_chans is the complement set of zap_channels
        isect = set(zap_channels).intersection(set(valid_chans))
        union = set(zap_channels).union(set(valid_chans))
        self.assertFalse(isect)
        self.assertTrue(union == set(all_channels))

        # Check output shapes
        self.assertEqual(mask.shape, (self.cube.num_subints, self.cube.num_bins))
        self.assertEqual(repvals.shape, self.cube.data.shape)

        ##### Check replacement of values behaves as expected #####
        # Once bad values have been replaced, if we call time_phase_mask() again
        # with the same params, then no previously flagged time-phase bins should be
        # flagged again.
        # NOTE: HOWEVER, new bins can still get flagged !
        # That is because once the old outliers have been replaced by "good" values, 
        # the range of acceptable value is reduced which may push previously "normal" points 
        # into outlier status.
        orig_data = self.cube.orig_data
        clean_data = apply_time_phase_mask(mask, valid_chans, repvals, orig_data)
        clean_cube = clfd.DataCube(clean_data)
        newmask, __, __ = clfd.time_phase_mask(clean_cube, q=q, zap_channels=zap_channels)

        # Check that no bin is flagged in both masks
        self.assertFalse(numpy.any(newmask & mask))

if __name__ == "__main__":
    unittest.main()
