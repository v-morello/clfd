# Changelog
All notable changes will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## 0.3.1 - 2019-11-19
### Added
- The `clfd` command line application now has a `-o` / `--outdir` option to save all data products to a single output directory

## 0.3.0 - 2019-07-20
### Added
- The latest release of `clfd` can now be easily installed via `pip install clfd`. 
- The setup script now defines a console script entry point `clfd` which points to the main function of `cleanup.py`. From the point of view of the user, this means a script called `clfd` is automatically placed in the `PATH`, which can be called from anywhere and that simply executes `cleanup.py`. This only works if using an installation method that actually executes the setup script, i.e. it won't work when just cloning the repository and placing it in the `PYTHONPATH`, in which case an alias named `clfd` for `cleanup.py` has to be defined manually.

### Changed
- The module name in `setup.py` has been changed from `clfd-pulsar` to simply `clfd`. The original decision was made to avoid potential name collisions, but `clfd` is not currently taken anywhere so let's make things simple from now on. *To avoid any trouble when upgrading to the new version, users should first cleanly uninstall any older versions of* `clfd`, by typing `pip uninstall clfd-pulsar`.
- Rearranged directory structure to make the module installable via `pip`. `apps`, `tests` and `example_data` are now subdirectories of `clfd`.
- Updated installation instructions in `README`
- Updated `README` with a word of warning on the `--despike` command line option

## 0.2.3 - 2019-07-17
### Fixed
- Dependency ``pytables`` in ``setup.py`` should be called ``tables`` when installed via ``pip``, apparently the same package has a different name on conda and PyPI.
- Removed relative import in ``report_plots.py`` that raised an error when using ``clfd`` with python 3+.
- Fixed a bug in ``cleanup.py`` where the list of features was not properly passed down to the core functions, which means that the list of features used was always the default triplet ``std, ptp, lfamp``.

### Added
- ``Report`` corner plot now displays the name of the report file.

## 0.2.2 - 2019-03-02
### Added
- ``Report`` now has two method to generate nice plots: ``corner_plot()`` and ``profile_mask_plot()``. The corner plot shows pairwise scatter plots of profile features and individual histograms, and the other shows the 2D profile mask along with the fraction of data masked in each channel and sub-integration.
- ``TODO.md`` with a list of planned features/upgrades/fixes.

### Changed
- Improved fix for float saturation issues: do not scale the data anymore when loading an archive into a DataCube, instead use float64 accumulators when computing profile variance and standard deviation. The ``DataCube`` property ``data`` now returns the original data with the baselines (i.e. profile median values) subtracted, while the property ``orig_data`` returns the data exactly as they are read from the archive.

## 0.2.1 - 2019-02-15
### Fixed
- DataCubes are now divided by the median absolute deviation (MAD) of non-zero values only. This avoids problems with archives where more than 50% of the data are equal to zero (may happen on GMRT data for example).
- psrchive interface ``get_frequencies()`` method now works with older psrchive versions, since the ``Archive.get_frequencies()`` method of psrchive seems to be only a recent addition (sometime in 2018).

### Added
- ``cleanup.py`` now has a ``--version`` option to print the version number of ``clfd`` and exit.
- Installing ``clfd`` using ``pip`` (via the ``make install`` command) now also installs the ``pytables`` module if not present.

## 0.2.0 - 2019-02-08
### Added
- The ``cleanup.py`` executable script now saves for each archive a ``Report`` object in HDF5 format. Reports contain all outputs produced by the cleaning process in a practical format, including: features, feature statistics (including min and max acceptable values for each), profile mask and time-phase mask (if the script was called with the ``--despike`` option). Note that saving and loading reports require the ``pytables`` python library.
- ``cleanup.py`` now has a ``--no-report`` option if the user does not wish to produce report(s), or does not have ``pytables``.
- The ``stats`` DataFrame returned by the ``profile_mask()`` function now contains the median of each feature
- New ``test()`` function that runs all unit tests
- Version of the module now stored in a unique location (``_version.py``)
- Format interfaces now have a ``get_frequencies()`` method

## 0.1.1 - 2019-01-16
### Added
- When loading an archive into a DataCube object, the data by are now divided by their overall median absolute deviation (MAD) after the baselines of each profile have been removed. This solves float32 saturation issues when computing some profile features (standard deviation and variance) on archives obtained from 8-bit Parkes ultra wide band receiver data. The data are still properly offset and scaled back before performing replacements (when using the `--despike` option).

## 0.1.0 - 2018-11-12
### Added
- First release of clfd