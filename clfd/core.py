from collections import OrderedDict

import numpy as np
import pandas
import clfd.features as pf

try:
    import psrchive
except:
    pass


class DataCube(object):
    """ Wrapper for three-dimensional folded data. The data order is
    (time, freq, phase) """

    def __init__(self, data, copy=False):
        """ Create DataCube instance from numpy array. 
        Classmethods are the preferred way of making a new DataCube instance. 

        Parameters
        ----------
        data: ndarray
            The folded data as a 3-dimensional array, in (time, freq, phase) order.
        copy: bool, optional
            If True, copy the input data. Otherwise the DataCube stores only a
            reference to 'data' to save memory (default: False)
        """
        if not type(data) == np.ndarray:
            raise ValueError("data must be a numpy array")
        if not len(data.shape) == 3:
            raise ValueError("data must be 3-dimensional")
        if not data.shape[0] * data.shape[1] >= 2:
            raise ValueError("data must have at least 2 profiles")
        if not data.shape[2] >= 2:
            raise ValueError("data must have at least 2 phase bins")

        if copy:
            self._data = data.copy()
        else:
            self._data = data

        self._subtract_baseline()

    def _subtract_baseline(self):
        """ Subtract from every profile its median value """
        nsubs, nchans, nbins = self.data.shape
        self._baselines = np.median(self.data, axis=2)
        self._data -= self._baselines.reshape(nsubs, nchans, 1)

    @property
    def data(self):
        """ 3D data """
        return self._data

    @property
    def orig_data(self):
        """ Original data, without baselines subtracted. """
        nsubs, nchans, nbins = self.data.shape
        return self.data + self.baselines.reshape(nsubs, nchans, 1)

    @property
    def baselines(self):
        """ 2D array with shape (num_subints, num_chans) containing the baselines of all profiles. """
        return self._baselines

    @property
    def num_subints(self):
        return self.data.shape[0]

    @property
    def num_chans(self):
        return self.data.shape[1]

    @property
    def num_bins(self):
        return self.data.shape[2]

    @property
    def subbands(self):
        """ Sum of the data along the time axis. Output data order is (time, phase). """
        return self.data.sum(axis=0)

    @property
    def subints(self):
        """ Sum of the data along the frequency axis. Output data order is (freq, phase). """
        return self.data.sum(axis=1)

    def save_npy(self, fname, dtype=np.float32):
        """ Save original 3D data to .npy file """
        nsubs, nchans, nbins = self.data.shape
        np.save(fname, self.orig_data.astype(dtype))

    @classmethod
    def from_npy(cls, fname):
        """ Load numpy array saved as a .npy file. """
        data = np.load(fname)
        return cls(data)

    @classmethod
    def from_psrchive(cls, archive):
        """ Create DataCube from PSRCHIVE Archive object. Only Stokes I data is read.
        
        Parameters
        ----------
        archive: str or psrchive.Archive
            Archive file (or object) to load.

        Returns
        -------
        cube: DataCube
            DataCube instance wrapping Stokes I data.
        """
        if type(archive) == str:
            archive = psrchive.Archive_load(archive)

        # Extract Stokes I only
        # Data shape is (n_subints, n_channels, n_phase_bins)
        # NOTE: we do NOT dedisperse
        data = archive.get_data()[:, 0, :, :]
        return cls(data)

    def __str__(self):
        return "{:s}(shape=({:d}, {:d}, {:d}))".format(
            type(self).__name__,
            self.num_subints,
            self.num_chans,
            self.num_bins)

    def __repr__(self):
        return str(self)


def featurize(cube, features=("std", "ptp", "lfamp")):
    """ Compute specified set of features for every profile in the given DataCube.

    Parameters
    ----------
    cube: DataCube
        The data cube to featurize.
    features: list or tuple of strings
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

    index = pandas.MultiIndex.from_product(
        [range(cube.num_subints), range(cube.num_chans)], names=["subint", "channel"]
    )
    data = OrderedDict()
    for fn in features:
        func = getattr(pf, fn)
        data[fn] = func(cube).ravel()

    table = pandas.DataFrame(data, index=index)
    return table


def feature_stats(features, q=2.0):
    """ Compute quartiles, inter-quartile range and min/max acceptable values for every
    column in 'features' based on Tukey's rule for outliers.

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

    Returns
    -------
    stats: pandas.DataFrame
        DataFrame containing the results. Columns are individual features, and rows are 
        individual statistics (quartiles, iqr, min and max values).

    Examples
    --------

    An example output would look like:

               std       ptp     lfamp
    q1    0.025949  0.130252  0.173604
    q3    0.028379  0.152941  0.387956
    iqr   0.002430  0.022689  0.214352
    vmin  0.021090  0.084874 -0.255099
    vmax  0.033238  0.198319  0.816660
    """
    stats = features.quantile([0.25, 0.50, 0.75])
    stats = stats.rename({0.25: "q1", 0.50: "med", 0.75: "q3"})
    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - q * stats.loc["iqr"]
    stats.loc["vmax"] = stats.loc["q3"] + q * stats.loc["iqr"]
    return stats


def profile_mask(features, q=2.0, zap_channels=[]):
    """ Compute profile mask, flagging outliers.

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


def time_phase_mask(cube, q=4.0, zap_channels=[]):
    """ Compute a data mask based on the cube's time-phase plot (sum of the
    data along the frequency axis of the cube).

    Parameters
    ----------
    cube: DataCube
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
    valid_chans_mask = np.ones(cube.num_chans, dtype=bool)
    if zap_channels:
        valid_chans_mask[zap_channels] = False
    num_valid_chans = valid_chans_mask.sum()
    valid_chans = np.where(valid_chans_mask)[0]

    data = cube.data[:, valid_chans].sum(axis=1)
    pcts = np.percentile(data, [25, 50, 75], axis=0) # Q1, median, Q3 along time axis
    stats = pandas.DataFrame(pcts).rename({0: "q1", 1: "med", 2: "q3"})
    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - q * stats.loc["iqr"]
    stats.loc["vmax"] = stats.loc["q3"] + q * stats.loc["iqr"]

    mask = (data < stats.loc["vmin"].values) | (data > stats.loc["vmax"].values)

    nsubs, nchans, nbins = cube.data.shape
    # NOTE: Don't forget to offset replacement values by profile baselines
    repvals = stats.loc["med"].values / num_valid_chans + cube.baselines.reshape(nsubs, nchans, 1)
    return mask, valid_chans, repvals

