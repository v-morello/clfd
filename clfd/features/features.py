import numpy as np
import scipy.stats


def ptp(cube):
    """ Peak-to-peak difference """
    return cube.data.ptp(axis=-1)

def std(cube):
    """ Standard deviation """
    # NOTE: use a float64 accumulator to avoid saturation issues
    return cube.data.std(axis=-1, dtype=np.float64)

def var(cube):
    """ Variance """
    # NOTE: use a float64 accumulator to avoid saturation issues
    return cube.data.var(axis=-1, dtype=np.float64)

def lfamp(cube):
    """ Amplitude of second Fourier bin """
    ft = np.fft.rfft(cube.data, axis=-1)
    return abs(ft[:, :, 1])

def skew(cube):
    """ Skewness """
    # Must cast to float64 to avoid overflow
    return scipy.stats.skew(cube.data.astype(np.float64), axis=-1)

def kurtosis(cube):
    """ Excess kurtosis """
    # Must cast to float64 to avoid overflow
    return scipy.stats.kurtosis(cube.data.astype(np.float64), axis=-1)

def acf(cube):
    """ Autocorrelation function with a lag of 1 phase bin """
    X = cube.data
    v = X.var(axis=-1, dtype=np.float64)
    v[v == 0] = np.inf
    acov = np.mean(X[..., :-1] * X[..., 1:], dtype=np.float64, axis=-1)
    return acov / v