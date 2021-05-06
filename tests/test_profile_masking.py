import numpy as np

from clfd import (
    pf,
    featurize,
    mask_profile,
)


def test_features(cube):

    """
    Test the feature functions.
    """

    for feature in pf.values():
        out = feature(cube)
        assert out.shape == cube.shape[:2]


def test_profile_mask(cube):

    """
    Test clfd's ability to construct a profile mask.
    """

    features = featurize(cube, features=pf.keys())
    _, __ = mask_profile(cube=cube, features=features)

    (_, nchan, __) = cube.shape
    zapchans = np.arange(0, nchan, 2)
    _, mask = mask_profile(
        cube=cube,
        features=features,
        Q=1000.0,
        zapchans=zapchans,
    )
    assert np.all(mask[:, zapchans])