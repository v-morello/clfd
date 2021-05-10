from clfd import time_phz_mask


def test_time_phase_masking(cube):

    """
    Test clfd's ability to construct a time phase mask.
    """

    Q = 2.0
    zapchans = range(10)
    allchans = range(cube.nchan)

    mask, valid_chans, new_values = time_phz_mask(
        data=cube.data,
        Q=Q,
        zapchans=zapchans,
    )

    union = set(zapchans).union(set(valid_chans))
    isect = set(zapchans).intersection(set(valid_chans))
    assert not isect
    assert union == set(allchans)

    assert new_values.shape == cube.data.shape
    assert mask.shape == (cube.nsub, cube.nbin)