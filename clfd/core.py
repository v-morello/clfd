from collections import OrderedDict
from typing import Iterable

import numpy as np
import pandas
from numpy.typing import NDArray

import clfd.features as pf


def featurize(cube: NDArray, features: Iterable[str] = ("std", "ptp", "lfamp")):
    """Compute specified set of features for every profile in the given DataCube.

    Parameters
    ----------
    cube: NDArray
        The data cube to featurize as a numpy array of shape
        (num_subints, num_chans, num_bins)
    features: iterable of strings
        List of features to compute. These must name functions in the 'clfd.features' submodule.

    Returns
    -------
    features: pandas.DataFrame
        DataFrame containing the results. Columns are individual features, and rows are indexed
        by a pandas.MultiIndex (subint, channel).

    Examples
    --------

    >>> table = featurize(cube, features=('std', 'ptp', 'lfamp'))
    >>> print(table)
                         std       ptp     lfamp
    subint channel
    0      0        0.030225  0.139496  0.050769
           1        0.029482  0.156823  0.413427
           2        0.026617  0.134454  0.312459
           3        0.026048  0.120710  0.466601
           4        0.023539  0.128128  0.246164
    ...                  ...       ...       ...

    Extract values for subint index 3 and channel indexes 15 to 19 inclusive:

    >>> table.loc[3,15:19, :]
                         std       ptp     lfamp
    subint channel
    3      15       0.022803  0.112603  0.245692
           16       0.020720  0.121008  0.195285

    See pandas.MultiIndex documentation for advanced indexing/slicing.
    """
    for fn in features:
        if not hasattr(pf, fn):
            msg = "No function '{:s}' in the clfd.features sub-module".format(fn)
            raise ValueError(msg)

    num_subints, num_chans, __ = cube.shape
    index = pandas.MultiIndex.from_product(
        [range(num_subints), range(num_chans)], names=["subint", "channel"]
    )
    data = OrderedDict()
    for fn in features:
        func = getattr(pf, fn)
        data[fn] = func(cube).ravel()

    table = pandas.DataFrame(data, index=index)
    return table


def profile_mask(features, q=2.0, zap_channels=[]):
    """Compute profile mask, flagging outliers.

    Parameters
    ----------
    features: pandas.DataFrame
        Output of the featurize() function.
    q: float, optional (default: 2.0)
        Parameter that controls the min and max values that define the 'inlier' or
        'normality' range. For every feature, the first and third quartiles (Q1 and Q3)
        are calculated, and R = Q3 - Q1 is the interquartile range. The min and max
        acceptable values are then defined as:

        vmin = Q1 - q x R
        vmax = Q3 + q x R

        The original recommendation of Tukey is q = 1.5.
    zap_channels: list or array of ints
        Frequency channel indices to forcibly flag as outliers. These are excluded
        from the analysis as well, and they will not be considered when calculating
        the inlier range for every feature.

    Returns
    -------
    stats: pandas.DataFrame
        DataFrame containing the results. Columns are individual features, and rows are
        individual statistics (quartiles, iqr, min and max values).
    mask: ndarray
        A two dimensional boolean numpy array, with shape (num_subints, num_channels).
        A value of True means that the associated profile is an outlier.
    """
    do_zap = (zap_channels is not None) and (len(zap_channels) > 0)

    # Exclude specified channels from the statistical analysis
    if do_zap:
        X = features.drop(zap_channels, level=1)
    else:
        X = features

    # Statistics for each feature, excluding zapped channels
    stats = X.quantile([0.25, 0.50, 0.75])
    stats = stats.rename({0.25: "q1", 0.50: "med", 0.75: "q3"})
    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - q * stats.loc["iqr"]
    stats.loc["vmax"] = stats.loc["q3"] + q * stats.loc["iqr"]

    # Flag outliers, now including zapped channels again
    mask = (features > stats.loc["vmax"]) | (features < stats.loc["vmin"])
    mask = mask.sum(axis=1).values.astype(bool).reshape(features.index.levshape)

    # Forcibly mask zapped channels
    if do_zap:
        mask[:, zap_channels] = True
    return stats, mask


def time_phase_mask(cube: NDArray, q: float = 4.0, zap_channels: list[int] = []):
    """Compute a data mask based on the cube's time-phase plot (sum of the
    data along the frequency axis of the cube).

    Parameters
    ----------
    cube: NDArray
        The input data cube as a numpy array of shape
        (num_subints, num_chans, num_bins)
    q: float, optional (default: 4.0)
        Parameter that controls the min and max values that define the 'inlier' or
        'normality' range.
    zap_channels: list or array of ints, optional (default: [])
        Frequency channel indices to exclude from the outlier analysis.

    Returns
    -------
    mask: ndarray
        A two dimensional boolean numpy array, with shape (num_subints, num_bins).
        A value of True means that the associated time-phase bin is an outlier.
    valid_chans: ndarray
        List of channel indices that are not part of 'zap_channels'. In these
        valid channels, bad data values are allowed to be replaced.
    repvals: ndarray
        Three dimensional array with same shape as the input data cube, containing
        the appropriate replacement values for bad data points in the original archive.
        A bad time-phase bin with indices (i, j) means that
        orig_data[i, valid_chans, j] should be replaced by repvals[i, valid_chans, j].
    """
    num_subints, num_chans, __ = cube.shape
    valid_chans_mask = np.ones(num_chans, dtype=bool)
    if zap_channels:
        valid_chans_mask[zap_channels] = False
    num_valid_chans = valid_chans_mask.sum()
    valid_chans = np.where(valid_chans_mask)[0]

    # For the purposes of this masking algorithm, we need to manipulate
    # baseline-subtracted data
    baselines = np.median(cube, axis=2).reshape(num_subints, num_chans, 1)
    subtracted_data = cube - baselines

    subints = subtracted_data[:, valid_chans, :].sum(axis=1)
    pcts = np.percentile(subints, [25, 50, 75], axis=0)  # Q1, median, Q3 along time axis
    stats = pandas.DataFrame(pcts).rename({0: "q1", 1: "med", 2: "q3"})
    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - q * stats.loc["iqr"]
    stats.loc["vmax"] = stats.loc["q3"] + q * stats.loc["iqr"]

    mask = (subints < stats.loc["vmin"].values) | (subints > stats.loc["vmax"].values)

    repvals = baselines + stats.loc["med"].values / num_valid_chans
    return mask, valid_chans, repvals
