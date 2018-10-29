import numpy as np

def ptp(cube):
    """ Peak-to-peak difference """
    return cube.data.ptp(axis=2)

def std(cube):
    """ Standard deviation """
    return cube.data.std(axis=2)

def var(cube):
    """ Variance """
    return cube.data.var(axis=2)

def lfamp(cube):
    """ Amplitude of second Fourier bin """
    ft = np.fft.rfft(cube.data, axis=2)
    return abs(ft[:, :, 1])
