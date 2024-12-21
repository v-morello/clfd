from typing import Optional

import numpy as np
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


def acf(cube: NDArray):
    """Autocorrelation function with a lag of 1 phase bin"""
    X = cube
    m = X.mean(axis=-1, dtype=np.float64, keepdims=True)
    v = X.var(axis=-1, dtype=np.float64)
    v[v == 0] = np.inf
    acov = np.mean(
        (X[..., :-1] - m) * (X[..., 1:] - m), dtype=np.float64, axis=-1
    )
    return acov / v


def skew(cube: NDArray):
    """
    Skewness. Sample bias is not removed. Returns 0 for constant data.
    """
    # Work in float64 to avoid overflow
    m1 = cube.mean(axis=-1, keepdims=True, dtype=np.float64)
    m2 = _moment(cube, m1, 2, axis=-1)
    m3 = _moment(cube, m1, 3, axis=-1)
    with np.errstate(invalid="ignore"):
        return np.where(m2 == 0, 0.0, m3 / m2**1.5)


def kurtosis(cube: NDArray):
    """
    Excess kurtosis. Sample bias is not removed. Returns +inf for constant
    data.
    """
    # Work in float64 to avoid overflow
    m1 = cube.mean(axis=-1, keepdims=True, dtype=np.float64)
    m2 = _moment(cube, m1, 2, axis=-1)
    m4 = _moment(cube, m1, 4, axis=-1)
    with np.errstate(invalid="ignore"):
        return np.where(m2 == 0, np.inf, m4 / m2**2 - 3)


def _moment(
    x: NDArray, mean: NDArray, order: int, *, axis: Optional[int] = None
) -> NDArray:
    """
    Raw statistical moment; mean of data must be externally provided with the
    correct shape.
    """
    return np.mean((x - mean) ** order, axis=axis)
