import pandas
import numpy as np
from clfd import __version__

# pytables to save / load reports
try:
    import tables
    HAS_PYTABLES = True
except:
    HAS_PYTABLES = False

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except:
    HAS_MATPLOTLIB = False


def _check_hdf5_libs():
    if not HAS_PYTABLES:
        raise ImportError("pytables library not available, cannot save/load Reports")


def _check_matplotlib():
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib library not available")


class Report(object):
    """ An object that stores all inputs and outputs of a clfd run on a 
    DataCube. It can be saved to / loaded from HDF5. Reports are produced
    by the cleanup executable. There should be little need for end
    users to create a Report using the __init__ method, they should rather
    use the Report.load() method to load a previously saved file.

    Parameters
    ----------
    features: pandas.DataFrame
        features table returned by the featurize() function
    stats: pandas.DataFrame
        stats table returned by the featurize() function
    profmask: ndarray
        boolean profile mask returned by profile_mask()
    qmask: float
        Value of the Tukey parameter 'q' used when profile_mask() was called
    frequencies: ndarray
        Channel frequencies of the original archive in MHz
    zap_channels: list or ndarray, optional
        zap_channels argument that was passed to profile_mask()
        (default: [])
    tpmask: ndarray, optional
        Time-phase mask returned by time_phase_mask() if the function was
        called (when the cleanup executable is called with the 
        --despike option). If time_phase_mask() was NOT called, leave this
        parameter to None.
        (default: None)
    qspike: float, optional
        Value of the Tukey parameter 'q' used as an argument of 
        time_phase_mask(). If time_phase_mask() was NOT called, leave this
        parameter to None.
        (default: None)
    """
    def __init__(self, features, stats, profmask, qmask, frequencies, zap_channels=[], tpmask=None, qspike=None):
        self._features = features
        self._stats = stats
        self._profmask = profmask
        self._qmask = qmask
        self._frequencies = frequencies
        self._zap_channels = np.asarray(zap_channels, dtype=int)
        self._tpmask = tpmask
        self._qspike = qspike
        self._version = __version__

    def _set_version(self, version):
        """ Private method to override current version when loading an old Report from file """
        self._version = version

    @property
    def frequencies(self):
        """ Channel frequencies """
        return self._frequencies

    @property
    def features(self):
        """ features table (pandas.DataFrame) returned by the featurize() function """
        return self._features

    @property
    def feature_names(self):
        """ list of feature names used """
        return list(self.features.columns)

    @property
    def stats(self):
        """ stats table (pandas.DataFrame) returned by the featurize() function """
        return self._stats

    @property
    def profmask(self):
        """ Boolean profile mask (numpy array) returned by the profile_mask() function """
        return self._profmask

    @property
    def qmask(self):
        """ Value of the Tukey parameter 'q' used when profile_mask() was called """
        return self._qmask

    @property
    def zap_channels(self):
        """ zap_channels argument that was passed to profile_mask(), as a
        boolean numpy array """
        return self._zap_channels

    @property
    def tpmask(self):
        """ Time-phase mask returned by time_phase_mask() if the function was
        called (when the cleanup executable is called with the --despike 
        option). If time_phase_mask() was NOT called, tpmask will be None. """
        return self._tpmask

    @property
    def qspike(self):
        """ Value of the Tukey parameter 'q' used as an argument to 
        time_phase_mask(). If time_phase_mask() was NOT called, tpmask will be
        None.
        """
        return self._qspike

    @property
    def version(self):
        """ Version of clfd that was used to produce this Report """
        return self._version

    def scatter_plot(self):
        """ NOT IMPLEMENTED YET """
        _check_matplotlib()
        # TODO
        raise NotImplementedError
    
    def save(self, fname):
        """ Save Report to HDF5 file """
        _check_hdf5_libs()

        with tables.open_file(fname, mode='w') as h5file:
            header_group = h5file.create_group('/', 'header')
            items = header_group._v_attrs
            items['version'] = self.version
            items['qmask'] = self.qmask
            # NOTE: PyTables can properly store 'None'
            items['qspike'] = self.qspike

        with pandas.HDFStore(fname, mode='a') as store:
            # NOTE: pandas' HDF5 API depends on the pytables library
            # DO NOT USE append=True ! This creates a weird IOError when
            # loading reports with pandas <= 0.23. Opening the HDFStore
            # with mode='a' seems good enough already.
            self.features.to_hdf(store, 'features')
            self.stats.to_hdf(store, 'stats')

            # NOTE: convert numpy arrays to pandas.DataFrames for storage
            # We convert back to numpy arrays when loading
            pandas.DataFrame(self.profmask).to_hdf(store, 'profmask')
            pandas.DataFrame(self.frequencies).to_hdf(store, 'frequencies')
            pandas.DataFrame(self.zap_channels).to_hdf(store, 'zap_channels')

            if self.tpmask is not None:
                pandas.DataFrame(self.tpmask).to_hdf(store, 'tpmask')

    @classmethod
    def load(cls, fname):
        """ Load Report from HDF5 file """
        _check_hdf5_libs()

        with tables.open_file(fname, mode='r') as h5file:
            header_group = h5file.get_node(h5file.root, 'header')
            items = header_group._v_attrs
            version = items['version']
            qmask = items['qmask']
            qspike = items['qspike']

        with pandas.HDFStore(fname, mode='r') as store:
            features = pandas.read_hdf(store, 'features')
            stats = pandas.read_hdf(store, 'stats')

            # The remaining attributes are numpy arrays, hence the .values
            profmask = pandas.read_hdf(store, 'profmask').values

            # NOTE: .ravel() must be called because DataFrames store
            # flat arrays as a column, i.e. shape = (N, 1)
            frequencies = pandas.read_hdf(store, 'frequencies').values.ravel()

            # NOTE: it looks like pandas.to_hdf simply does not write out 
            # empty arrays, hence these try blocks below
            try:
                # call .ravel() here as well to get a 1D array
                zap_channels = pandas.read_hdf(store, 'zap_channels').values.ravel()
            except KeyError:
                zap_channels = np.asarray([], dtype=int)

            try:
                tpmask = pandas.read_hdf(store, 'tpmask').values
            except KeyError:
                tpmask = None

        report = cls(features, stats, profmask, qmask, frequencies, zap_channels, tpmask=tpmask, qspike=qspike)
        # NOTE: don't forget to override version to the one read from file
        report._set_version(version)
        return report
