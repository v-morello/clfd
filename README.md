# clfd

``clfd`` stands for **cl**ean **f**olded **d**ata, and implements smart interference removal algorithms to be used on _folded_ pulsar search and pulsar timing data. They are based on a simple outlier detection method and require very little to no human input, which is the main reason for their efficacy. These cleaning algorithms were initially developed for a complete re-processing of the High Time Resolution Universe (HTRU) survey, and can be credited with the discovery of several pulsars that would have otherwise been missed. 

### Citation

If using ``clfd`` contributes to a project that leads to a scientific publication, please cite the article

["The High Time Resolution Universe survey XIV: Discovery of 23 pulsars through GPU-accelerated reprocessing"](https://arxiv.org/abs/1811.04929)

A detailed explanation of ``clfd``'s algorithms and a visual demonstration of what they can do on real Parkes data can be found in section 2.4.

### Interfaces to existing data formats

The implementation of the cleaning algorithms is entirely decoupled from the input/output data format, and interfaces to any folded data format can be easily implemented. Currently, ``clfd`` can read and write PSRFITS archives via the python bindings of [PSRCHIVE](http://psrchive.sourceforge.net/), which are not a strict dependency but warmly recommended anyway. An interface to [PRESTO](https://www.cv.nrao.edu/~sransom/presto/)'s pfd archives will be added if there are any expressions of interest.

### Python version

The core of ``clfd`` is fully compatible with both python 2.7 and python 3, but note that the python bindings of [PSRCHIVE](http://psrchive.sourceforge.net/) work only with python <= 2.7 on most systems. Keep that in mind if you are planning to install ``clfd`` in a virtual environment with [conda](https://conda.io/docs/user-guide/tasks/manage-environments.html) or any similar alternative.


### Dependencies

Strict dependencies:

- ``numpy``
- ``pandas``

Optional but recommended:

- ``pytables``: to save and load cleaning reports in HDF5 format

### Installation

Clone the repository into the directory of your choice, and run

```bash
cd clfd
make install
```

This simply runs ``pip install`` in [editable mode](https://pip.pypa.io/en/latest/reference/pip_install/#editable-installs), and installs all required dependencies with ``pip``. If you are not allowed to install packages with ``pip`` (this may be the case on some computing clusters), then you can simply add the root directory of ``clfd`` to your ``PYTHONPATH`` environment variable. After that we can run the unit tests for good measure:

```bash
$ make tests
python -m unittest discover clfd/tests
..............
----------------------------------------------------------------------
Ran 14 tests in 0.214s

OK
```

Note that if the PSRCHIVE python bindings cannot be imported, then all PSRCHIVE-related tests will be skipped, which will visible in the output above. Tests related to saving / loading reports will also be skipped if ``pytables`` is not available.

### Command line usage

There is a ``cleanup.py`` script in the ``apps`` sub-directory that allows batch processing of multiple files / archives at once. For detailed help on command line arguments:

```bash
cd apps/
python cleanup.py -h
```

In the example below, we process all psrchive folded archives in the ``~/folded_data`` directory using 8 processes in parallel. The profile masking algorithm uses the same three features as in the paper with a Tukey parameter (``qmask``) of 2.0. ``--despike`` enables the use of the zero DM spike removal algorithm, which has its own Tukey parameter (``qspike``, 4.0 in the example here). The spike removal is turned off by default as there is a small chance that it could affect pulses from a very bright low-DM pulsar, and it also tends to fail in the worst RFI environments.

```bash
python cleanup.py ~/folded_data/*.ar --fmt psrchive --features std ptp lfamp --qmask 2.0 --despike --qspike 4.0 --processes 8
```

Every clean archive is saved in the directory where its associated input archive is found, with the an additional ``.clfd`` extension appended. Report files in HDF5 format are also saved as ``BASENAME_clfd_report.h5`` where ``BASENAME`` is the archive file name without its extension. A Report stores all inputs and outputs of a clfd run on an archive, they can easily be loaded and manipulated interactively in IPython:

```python
>>> from clfd import Report
>>> r = Report.load("SomeArchive_clfd_report.h5")
```

See section "Working with reports" below for more details.


### Interactive Usage

The ``cleanup.py`` script may be the most practical way of getting the job done, but it just calls functions that are accessible to the user as well. It might be useful to check or plot intermediate outputs. The example below exposes the computation steps: featurization, outlier flagging and application of the outlier mask to the original archive.

```python
>>> import psrchive
>>> import clfd

# Load folded archive produced with PSRCHIVE
>>> cube = clfd.DataCube.from_psrchive("archive.ar")

# Compute chosen profile features.
# The output is a pandas DataFrame with feature names as columns, and (subint, channel) tuples as rows.
>>> features = clfd.featurize(cube, features=('std', 'ptp', 'lfamp'))
>>> print(features)
                     std       ptp     lfamp
subint channel                              
0      0        0.042826  0.224936  0.786012
       1        0.000210  0.003367  0.003367
       2        0.002779  0.006757  0.009283
       3        0.002778  0.006757  0.020955
...                  ...       ...       ...
57     1020     0.050708  0.309764  0.171277
       1021     0.048685  0.272727  0.928349
       1022     0.055210  0.314584  1.463649
       1023     0.058338  0.346801  1.077389

[59392 rows x 3 columns]

# From there, compute profile mask, optionally excluding some known bad channels from the analysis. 
# The example archive here contains Parkes BPSR data, and we know that the first 150 channels are always bad.
>>> stats, mask = clfd.profile_mask(features, q=2.0, zap_channels=range(150))

# 'stats' contains the 1st and 3rd quantiles, inter-quartile range and min/max acceptable values for each feature.
# vmin = q1 - q x iqr
# vmax = q3 + q x iqr
# Where 'q' is the parameter passed to the profile_mask function above.
>>> print(stats)

           std       ptp     lfamp
q1    0.037299  0.202817  0.376125
q3    0.040031  0.235003  0.918363
iqr   0.002733  0.032185  0.542239
vmin  0.031833  0.138447 -0.708352
vmax  0.045497  0.299373  2.002841

# 'mask' is a boolean array of shape (num_subints, num_channels), whose value is True for bad profiles.
# Any frequency channels specified via the 'zap_channels' argument above are forcibly set to True
>>> mask.shape
(58, 1024)

>>> mask
array([[ True,  True,  True, ..., False, False, False],
       [ True,  True,  True, ..., False, False, False],
       [ True,  True,  True, ..., False, False, False],
       ...,
       [ True,  True,  True, ..., False, False, False],
       [ True,  True,  True, ..., False, False, False],
       [ True,  True,  True, ...,  True,  True,  True]])

# Applying the mask to the original archive and saving the output is a format-dependent operation. 
# For each format there is a corresponding Handler class in the clfd.handlers sub-module, which implements methods to apply a mask to the original file and save the output.
>>> from clfd.interfaces import PsrchiveInterface

# In PSRCHIVE, every profile has a weight parameter. This sets the weight of every bad profile to 0.
# We can then save the clean data as a new archive in PSRFITS format.
>>> PsrchiveInterface.apply_profile_mask(mask, archive)
>>> PsrchiveInterface.save("archive_clean.ar", archive)

# Optionally, we can then use the zero DM spike removal algorithm. Here the idea is to look for
# outliers in the zero DM time-phase plot, and replace them by appropriate values (inferred 
# from the data) across the frequency dimension.
>>> tpmask, valid_chans, repvals = clfd.time_phase_mask(cube, q=4.0, zap_channels=zap_channels)

# 'mask' is a boolean array of shape (num_subints, num_phase_bins), whose value is True for bad time-phase bins.
# 'valid_chans' is the list of channels NOT included in zap_channels
# 'repvals' is a numpy array with the same shape as the data cube, containing appropriate replacement values
>>> PsrchiveInterface.apply_time_phase_mask(tpmask, valid_chans, repvals, archive)
>>> PsrchiveInterface.save("archive_cleanest.ar", archive)
```

### Working with reports

Running the ``cleanup.py`` script produces report files by default with some useful informations about the cleaning performed. Reports store all inputs and outputs of a clfd run on an archive. **NOTE: Reports are very much a feature in development and may change in the future**. At the moment (``v0.2.0`` and above), a Report object has the following attributes:

- ``frequencies``: channel frequencies in MHz
- ``feature_names``: list of feature names used
- ``features``: pandas.DataFrame returned by the ``featurize()`` function
- ``stats``: pandas.DataFrame returned by the ``featurize()`` function
- ``profmask``: boolean profile mask returned by the ``profile_mask()`` function. This is a numpy array with shape (num_subints, num_channels)
- ``qmask``: value of the Tukey parameter ``q`` passed to ``profile_mask()``
- ``zap_channels``: zap_channels argument that passed to ``profile_mask()``
- ``tpmask``: mask returned by ``time_phase_mask()`` if the function was called (i.e. when the cleanup executable is called with the ``--despike`` option). If time_phase_mask() was NOT called, tpmask will be ``None``. Otherwise, ``tpmask`` is a numpy array with shape (num_subints, num_phase_bins).
- ``qspike``: value of the Tukey parameter 'q' passed to ``time_phase_mask()``. If ``time_phase_mask()`` was NOT called, tpmask will be ``None``.
- ``version``: version of clfd that was used to produce this report.

More attributes may be added in future versions, along with convenience methods to generate plots. In the meantime, you can generate plots yourself using ``matplotlib``, for example:

```python
>>> import matplotlib.pyplot as plt
>>> from clfd import Report
>>> r = Report.load("SomeArchive_clfd_report.h5")

# Masked profiles appear as black pixels
>>> plt.imshow(r.profmask, cmap='Greys')
>>> plt.title('Profile Mask')
>>> plt.xlabel('Channel Index')
>>> plt.ylabel('Sub-Integration Index')
```