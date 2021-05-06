import numpy as np

from clfd import mask_time_phz


def test_time_phase_masking(cube):

    """
    Test clfd's ability to construct a time phase mask.
    """

    (nsubs, nchans, nbins) = cube.shape

    Q = 2.0
    zapchans = range(10)
    allchans = range(nchans)

    mask, vchans, vnew = mask_time_phz(
        cube=cube,
        Q=Q,
        zapchans=zapchans,
    )

    union = set(zapchans).union(set(vchans))
    isect = set(zapchans).intersection(set(vchans))
    assert not isect
    assert union == set(allchans)

    assert vnew.shape == cube.shape
    assert mask.shape == (nsubs, nbins)

    new_mask, __, __ = mask_time_phz(
        cube=cube,
        Q=Q,
        zapchans=zapchans,
    )
    assert not np.any(new_mask & mask)