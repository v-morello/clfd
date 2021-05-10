from clfd import mask_time_phz


def test_time_phase_masking(cube):

    """
    Test clfd's ability to construct a time phase mask.
    """

    Q = 2.0
    zapchans = range(10)
    allchans = range(cube.nchan)

    mask, vchans, vnew = mask_time_phz(
        cube=cube,
        Q=Q,
        zapchans=zapchans,
    )

    union = set(zapchans).union(set(vchans))
    isect = set(zapchans).intersection(set(vchans))
    assert not isect
    assert union == set(allchans)

    assert vnew.shape == cube.data.shape
    assert mask.shape == (cube.nsub, cube.nbin)