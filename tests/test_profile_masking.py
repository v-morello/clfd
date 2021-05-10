import numpy as np

from clfd import (
    featurize,
    profile_mask,
    profile_features,
)


def test_features(cube):

    """
    Test the feature functions.
    """

    for feature in profile_features.values():
        out = feature(cube.data)
        assert out.shape == cube.data.shape[:2]


def test_profile_mask(cube):

    """
    Test clfd's ability to construct a profile mask.
    """

    features = featurize(cube.data, features=profile_features.keys())
    _, __ = profile_mask(features=features)

    zapchans = np.arange(0, cube.nchan, 2)
    _, mask = profile_mask(
        features=features,
        Q=1000.0,
        zapchans=zapchans,
    )
    assert np.all(mask[:, zapchans])