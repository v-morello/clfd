from pathlib import Path

import numpy
import numpy as np
import pytest

from clfd import ArchiveWrapper, profile_mask, time_phase_mask

from .utils import HAS_PSRCHIVE


@pytest.fixture(name="archive_path")
def fixture_archive_path() -> Path:
    return Path(__file__).parent / ".." / "example_data" / "psrchive_example.ar"


@pytest.fixture(name="archive_wrapper")
def fixture_archive_wrapper(archive_path: Path) -> ArchiveWrapper:
    return ArchiveWrapper(archive_path)


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_channel_frequencies_attribute(archive_wrapper: ArchiveWrapper):
    nchan = 128
    foff = -3.125
    fch1 = 1580.43701172
    expected_frequencies = fch1 + foff * numpy.arange(nchan)
    assert np.allclose(archive_wrapper.channel_frequencies, expected_frequencies)


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_profile_masked_archive_is_saved_with_expected_weights(archive_path: Path, tmp_path: Path):
    wrapper = ArchiveWrapper(archive_path)
    cube = wrapper.data_cube()

    result = profile_mask(cube, features=["std", "ptp", "lfamp"], q=2.0, zap_channels=range(10))
    wrapper.apply_profile_mask(result.mask)
    output_path = tmp_path / "archive.ar"
    wrapper.save(output_path)

    wrapper = ArchiveWrapper(output_path)
    assert np.array_equal(wrapper._archive.get_weights() == 0.0, result.mask)


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_time_phase_masked_archive_is_saved_with_expected_replacement_values(
    archive_path: Path, tmp_path: Path
):
    wrapper = ArchiveWrapper(archive_path)
    cube = wrapper.data_cube()

    q = 2.0
    zap_channels = range(10)
    result = time_phase_mask(cube, q=q, zap_channels=zap_channels)
    wrapper.apply_time_phase_mask(result)

    output_path = tmp_path / "archive.ar"
    wrapper.save(output_path)

    wrapper = ArchiveWrapper(output_path)
    cube = wrapper.data_cube()

    for i, j in zip(*np.where(result.mask)):
        assert np.allclose(
            cube[i, result.valid_channels, j],
            result.replacement_values[i, result.valid_channels, j],
        )
