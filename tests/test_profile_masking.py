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


def load_features():
    """ Returns a list of tuples (feature_name, featurizer_function) """
    return inspect.getmembers(clfd.features, inspect.isfunction)


class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.cube = load_test_datacube()
        self.functions = load_features()

    def test_features(self):
        for name, func in self.functions:
            out = func(self.cube)
            self.assertEqual(out.shape, self.cube.data.shape[:2])


class TestFeaturize(unittest.TestCase):
    def setUp(self):
        self.cube = load_test_datacube()
        self.feature_names = [name for name, func in load_features()]
        self.num_features = len(self.feature_names)

    def test_featurize(self):
        for n in range(self.num_features):
            data = clfd.featurize(self.cube, features=self.feature_names[:n+1])
    

class TestProfileMask(unittest.TestCase):
    def setUp(self):
        self.cube = load_test_datacube()
        self.feature_names = [name for name, func in load_features()]

    def test_profile_mask(self):
        data = clfd.featurize(self.cube, features=self.feature_names)

        # Without specifying zapped channels
        stats, mask = clfd.profile_mask(data, zap_channels=[])

        # With specifying zapped channels
        # Ensure that those zapped channels are indeed masked in the output mask
        zap_channels = numpy.arange(0, self.cube.num_chans, 2)
        stats, mask = clfd.profile_mask(data, zap_channels=zap_channels, q=1000.0)
        self.assertTrue(numpy.all(mask[:, zap_channels]))






if __name__ == "__main__":
    unittest.main()
