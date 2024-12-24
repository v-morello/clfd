import inspect
import os
import unittest
from typing import Callable

import numpy
import pytest
from numpy.typing import NDArray

import clfd
import clfd.features

from .utils import get_example_data_path


def load_test_datacube():
    fname = os.path.join(get_example_data_path(), "npy_example.npy")
    return numpy.load(fname)


def load_features():
    """Returns a list of tuples (feature_name, featurizer_function)"""
    return inspect.getmembers(clfd.features, inspect.isfunction)


@pytest.fixture(name="data_cube")
def fixture_data_cube() -> NDArray:
    fname = os.path.join(get_example_data_path(), "npy_example.npy")
    return numpy.load(fname)


FEATURES: list[tuple[str, Callable]] = inspect.getmembers(clfd.features, inspect.isfunction)


@pytest.mark.parametrize(
    "feature", [func for _, func in FEATURES], ids=[name for name, _ in FEATURES]
)
def test_feature_returns_ndarray_with_expected_shape(data_cube: NDArray, feature: Callable):
    result = feature(data_cube)
    assert isinstance(result, numpy.ndarray)
    assert result.shape == data_cube.shape[:2]


class TestFeaturize(unittest.TestCase):
    def setUp(self):
        self.cube = load_test_datacube()
        self.feature_names = [name for name, __ in load_features()]
        self.num_features = len(self.feature_names)

    def test_featurize(self):
        for n in range(self.num_features):
            clfd.featurize(self.cube, features=self.feature_names[: n + 1])


class TestProfileMask(unittest.TestCase):
    def setUp(self):
        self.cube = load_test_datacube()
        self.feature_names = [name for name, func in load_features()]

    def test_profile_mask(self):
        data = clfd.featurize(self.cube, features=self.feature_names)

        # Without specifying zapped channels
        __, mask = clfd.profile_mask(data, zap_channels=[])

        # With specifying zapped channels
        # Ensure that those zapped channels are indeed masked in the output mask
        num_chans = self.cube.shape[1]
        zap_channels = numpy.arange(0, num_chans, 2)
        __, mask = clfd.profile_mask(data, zap_channels=zap_channels, q=1000.0)
        self.assertTrue(numpy.all(mask[:, zap_channels]))


if __name__ == "__main__":
    unittest.main()
