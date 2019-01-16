# Changelog
All notable changes will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.1.1 - 2019-01-16
### Added
- When loading an archive into a DataCube object, the data by are now divided by their overall median absolute deviation after the baselines of each profile have been removed. This solves float32 saturation issues when computing some profile features (standard deviation and variance) on archives obtained from 8-bit Parkes ultra wide band receiver data. The data are still properly offset and scaled back before performing replacements (when using the `--despike` option).

## 0.1.0 - 2018-11-12
### Added
- First release of clfd