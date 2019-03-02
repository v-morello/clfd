### Upgrades and new features
- Add before/after plots to the ``Report`` class, to evaluate the effect of cleaning on the archive's sub-bands, sub-integrations and folded profile.
- Add a new python app to evaluate the RFI situation in an observation file directly. The idea would be to run ``dspsr`` to fold the observation at a certain period T(say T=1 second), then run clfd on the resulting archive to obtain a tim-dependent channel mask with a time resolution of T.
