# clfd

![Tests][tests]
[![Coverage Status][coveralls-badge]][coveralls]
[![Code style: black][black-badge]][black]
[![arXiv][arXiv-badge]][arXiv]
![LICENSE][license-badge]
![Python versions][pyversions-badge]

## Smart RFI removal algorithms to be used on folded pulsar search and timing data

[**clfd**][clfd] stands for **cl**ean **f**olded **d**ata, and implements smart interference removal algorithms to be used on *folded* pulsar search and pulsar timing data. They are based on a simple outlier detection method and require very little to no human input, which is the main reason for their efficacy. These cleaning algorithms were initially developed for a complete re-processing of the **H**igh **T**ime **R**esolution **U**niverse (**HTRU**) survey, and can be credited with the discovery of several pulsars that would have otherwise been missed.

## Citation

If using [**clfd**][clfd] contributes to a project that leads to a scientific publication, please cite the article ["*The High Time Resolution Universe survey XIV: Discovery of 23 pulsars through GPU-accelerated reprocessing*"][arXiv].

A detailed explanation of [**clfd**][clfd]'s algorithms and a visual demonstration of what they can do on real Parkes data can be found in section 2.4. The idea is to convert each profile (there is one profile per channel and per sub-integration) to a small set of representative features (e.g. standard deviation, peak-to-peak difference) and to flag outliers in the resulting feature space. Since v0.2.2, [**clfd**][clfd]  outputs report plots to visualize the outlier flagging process and the resulting two-dimensional time-frequency mask applied to the clean archive. Here's the output of a [**clfd**][clfd] run on a Parkes observation of the pulsar J0735-62, where the red lines delimit the automatically inferred acceptable value range for each feature:

[clfd]: https://github.com/v-morello/clfd
[tests]: https://github.com/v-morello/clfd/actions/workflows/tests.yaml/badge.svg
[black]: https://github.com/psf/black
[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[coveralls]: https://coveralls.io/github/v-morello/clfd?branch=main
[coveralls-badge]: https://coveralls.io/repos/github/v-morello/clfd/badge.svg?branch=main
[arXiv]: https://arxiv.org/abs/1811.04929
[arXiv-badge]: http://img.shields.io/badge/astro.ph-1811.04929-B31B1B.svg
[license-badge]: https://img.shields.io/badge/License-MIT-green.svg
[pyversions-badge]: https://img.shields.io/pypi/pyversions/clfd.svg
