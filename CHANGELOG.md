# Changelog
All notable changes will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.2.0 - 2019-02-08
### Added
- The ```cleanup.py``` executable script now saves for each archive a ```Report``` object in HDF5 format. Reports contain all outputs produced by the cleaning process in a practical format, including: features, feature statistics (including min and max acceptable values for each), profile mask and time-phase mask (if the script was called with the ```--despike``` option). Note that saving and loading reports require the ```pytables``` python library.
- ```cleanup.py``` now has a ```--no-report``` option if the user does not wish to produce report(s), or does not have ```pytables```.
- The ```stats``` DataFrame returned by the ```profile_mask()``` function now contains the median of each feature
- New ```test()``` function that runs all unit tests
- Version of the module now stored in a unique location (```_version.py```)
- Format interfaces now have a ```get_frequencies()``` method

## 0.1.1 - 2019-01-16
### Added
- When loading an archive into a DataCube object, the data by are now divided by their overall median absolute deviation after the baselines of each profile have been removed. This solves float32 saturation issues when computing some profile features (standard deviation and variance) on archives obtained from 8-bit Parkes ultra wide band receiver data. The data are still properly offset and scaled back before performing replacements (when using the `--despike` option).

## 0.1.0 - 2018-11-12
### Added
- First release of clfd