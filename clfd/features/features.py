import numpy as np
import scipy.stats
from numpy.typing import NDArray


def ptp(cube: NDArray):
    """Peak-to-peak difference"""
    return cube.ptp(axis=-1)


def std(cube: NDArray):
    """Standard deviation"""
    # NOTE: use a float64 accumulator to avoid saturation issues
    return cube.std(axis=-1, dtype=np.float64)


def var(cube: NDArray):
    """Variance"""
    # NOTE: use a float64 accumulator to avoid saturation issues
    return cube.var(axis=-1, dtype=np.float64)


def lfamp(cube: NDArray):
    """Amplitude of second Fourier bin"""
    ft = np.fft.rfft(cube, axis=-1)
    return abs(ft[:, :, 1])


def skew(cube: NDArray):
    """Skewness"""
    # Must cast to float64 to avoid overflow
    return scipy.stats.skew(cube.astype(np.float64), axis=-1)


def kurtosis(cube: NDArray):
    """Excess kurtosis"""
    # Must cast to float64 to avoid overflow
    return scipy.stats.kurtosis(cube.astype(np.float64), axis=-1)


def acf(cube: NDArray):
    """Autocorrelation function with a lag of 1 phase bin"""
    X = cube
    v = X.var(axis=-1, dtype=np.float64)
    v[v == 0] = np.inf
    acov = np.mean(X[..., :-1] * X[..., 1:], dtype=np.float64, axis=-1)
    return acov / v
