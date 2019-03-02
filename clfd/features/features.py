import numpy as np

def ptp(cube):
    """ Peak-to-peak difference """
    return cube.data.ptp(axis=2)

def std(cube):
    """ Standard deviation """
    # NOTE: use a float64 accumulator to avoid saturation issues
    return cube.data.std(axis=2, dtype=np.float64)

def var(cube):
    """ Variance """
    # NOTE: use a float64 accumulator to avoid saturation issues
    return cube.data.var(axis=2, dtype=np.float64)

def lfamp(cube):
    """ Amplitude of second Fourier bin """
    ft = np.fft.rfft(cube.data, axis=2)
    return abs(ft[:, :, 1])
