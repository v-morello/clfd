from pathlib import Path

import numpy as np

from clfd import ArchiveHandler, find_time_phase_spikes, profile_mask

from .utils import skip_unless_psrchive_installed


@skip_unless_psrchive_installed
def test_profile_masked_archive_is_saved_with_expected_weights(
    archive_path: Path, tmp_path: Path
):
    handler = ArchiveHandler(archive_path)
    cube = handler.data_cube()

    result = profile_mask(
        cube, features=["std", "ptp", "lfamp"], q=2.0, zap_channels=range(10)
    )
    handler.apply_profile_mask(result.mask)
    output_path = tmp_path / "archive.ar"
    handler.save(output_path)

    handler = ArchiveHandler(output_path)
    assert np.array_equal(handler._archive.get_weights() == 0.0, result.mask)


@skip_unless_psrchive_installed
def test_apply_spike_subtraction_plan_replaces_bad_data_as_expected(
    archive_path: Path, tmp_path: Path
):
    handler = ArchiveHandler(archive_path)
    cube = handler.data_cube()

    q = 2.0
    zap_channels = range(10)
    result, plan = find_time_phase_spikes(cube, q=q, zap_channels=zap_channels)
    handler.apply_spike_subtraction_plan(plan)

    output_path = tmp_path / "archive.ar"
    handler.save(output_path)

    handler = ArchiveHandler(output_path)
    cube = handler.data_cube()

    for i, j in zip(*np.where(result.mask)):
        assert np.allclose(
            cube[i, plan.valid_channels, j],
            plan.replacement_values[i, plan.valid_channels, j],
        )
