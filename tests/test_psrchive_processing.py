from pathlib import Path

import numpy
import numpy as np
import pytest

from clfd import ArchiveWrapper, featurize, profile_mask, time_phase_mask

from .utils import HAS_PSRCHIVE


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
@pytest.fixture(name="archive_path")
def fixture_archive_path() -> Path:
    return Path(__file__).parent / ".." / "example_data" / "psrchive_example.ar"


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
@pytest.fixture(name="archive_wrapper")
def fixture_archive_wrapper(archive_path: Path) -> ArchiveWrapper:
    return ArchiveWrapper.fromfile(archive_path)


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_channel_frequencies_attribute(archive_wrapper: ArchiveWrapper):
    nchan = 128
    foff = -3.125
    fch1 = 1580.43701172
    expected_frequencies = fch1 + foff * numpy.arange(nchan)
    assert np.allclose(archive_wrapper.channel_frequencies, expected_frequencies)


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_profile_masked_archive_is_saved_with_expected_weights(archive_path: Path, tmp_path: Path):
    wrapper = ArchiveWrapper.fromfile(archive_path)
    cube = wrapper.data_cube()
    features = featurize(cube, features=["std", "ptp", "lfamp"])
    __, mask = profile_mask(features, q=2.0, zap_channels=range(10))
    wrapper.apply_profile_mask(mask)

    output_path = tmp_path / "archive.ar"
    wrapper.save(output_path)

    wrapper = ArchiveWrapper.fromfile(output_path)
    assert np.array_equal(wrapper._archive.get_weights() == 0.0, mask)


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_time_phase_masked_archive_is_saved_with_expected_replacement_values(
    archive_path: Path, tmp_path: Path
):
    wrapper = ArchiveWrapper.fromfile(archive_path)
    cube = wrapper.data_cube()

    q = 2.0
    zap_channels = range(10)
    mask, valid_chans, repvals = time_phase_mask(cube, q=q, zap_channels=zap_channels)
    wrapper.apply_time_phase_mask(mask, valid_chans, repvals)

    output_path = tmp_path / "archive.ar"
    wrapper.save(output_path)

    wrapper = ArchiveWrapper.fromfile(output_path)
    cube = wrapper.data_cube()

    for i, j in zip(*np.where(mask)):
        assert np.allclose(
            cube.data[i, valid_chans, j],
            repvals[i, valid_chans, j],
        )
