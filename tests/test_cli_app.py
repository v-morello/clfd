import subprocess
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from clfd import Report
from clfd.apps.cleanup import run_program
from clfd.apps.functions import load_zapfile

from .utils import skip_unless_psrchive_installed


def test_cli_app_entrypoint_exists():
    exit_code = subprocess.check_call(["clfd", "--help"])
    assert exit_code == 0


def test_load_zapfile_on_non_empty_zapfile(
    tmp_path_factory: pytest.TempPathFactory,
):
    channels = [1, 42]
    path = tmp_path_factory.mktemp("zapfile") / "zapfile.txt"
    with open(path, "w") as file:
        file.write("\n".join(map(str, channels)))
    assert load_zapfile(path) == channels


def test_load_zapfile_on_empty_zapfile(
    tmp_path_factory: pytest.TempPathFactory,
):
    path = tmp_path_factory.mktemp("zapfile") / "zapfile.txt"
    open(path, "w").close()
    assert load_zapfile(path) == []


@skip_unless_psrchive_installed
def test_cli_app_with_spike_removal(
    tmp_path_factory: pytest.TempPathFactory,
    archive_path: Path,
    expected_profmask: NDArray,
    expected_tpmask: NDArray,
):
    """
    Basic end-to-end test of the CLI app on a PSRCHIVE archive.
    """
    outdir = Path(tmp_path_factory.mktemp("clfd_outdir"))
    args = [
        "--despike",
        "--qspike",
        str(2.0),
        "--outdir",
        str(outdir),
        str(archive_path),
    ]
    run_program(args)

    expected_archive_path = outdir / "psrchive_example.ar.clfd"
    assert expected_archive_path.exists()

    expected_report_path = outdir / "psrchive_example_clfd_report.json"
    assert expected_report_path.exists()

    expected_plot_path = outdir / "psrchive_example_clfd_report.png"
    assert expected_plot_path.exists()

    report = Report.load(expected_report_path)
    assert np.array_equal(
        report.profile_masking_result.mask, expected_profmask
    )
    assert np.array_equal(report.spike_finding_result.mask, expected_tpmask)


@skip_unless_psrchive_installed
def test_cli_app_without_spike_removal(
    tmp_path_factory: pytest.TempPathFactory,
    archive_path: Path,
    expected_profmask: NDArray,
):
    outdir = Path(tmp_path_factory.mktemp("clfd_outdir"))
    args = [
        "--outdir",
        str(outdir),
        str(archive_path),
    ]
    run_program(args)

    expected_archive_path = outdir / "psrchive_example.ar.clfd"
    assert expected_archive_path.exists()

    expected_report_path = outdir / "psrchive_example_clfd_report.json"
    assert expected_report_path.exists()

    expected_plot_path = outdir / "psrchive_example_clfd_report.png"
    assert expected_plot_path.exists()

    report = Report.load(expected_report_path)
    assert np.array_equal(
        report.profile_masking_result.mask, expected_profmask
    )
    assert report.spike_finding_result is None


@skip_unless_psrchive_installed
def test_cli_app_rejects_bad_feature_names(archive_path: Path):
    args = [
        "--features",
        "std",
        "this_feature_name_does_not_exist",
        "ptp",
        str(archive_path),
    ]
    with pytest.raises(SystemExit):
        run_program(args)


@skip_unless_psrchive_installed
def test_cli_app_rejects_non_existent_output_dir(archive_path: Path):
    args = [
        "--outdir",
        "/non/existent/path",
        str(archive_path),
    ]
    with pytest.raises(SystemExit):
        run_program(args)


@skip_unless_psrchive_installed
def test_cli_app_reject_duplicate_input_file_names_if_outdir_is_specified(
    tmp_path_factory: pytest.TempPathFactory,
    archive_path: Path,
):
    outdir = Path(tmp_path_factory.mktemp("clfd_outdir"))
    args = [
        "--outdir",
        str(outdir),
        str(archive_path),
        str(Path("/some/other/path") / archive_path.name),
    ]
    with pytest.raises(ValueError):
        run_program(args)


@skip_unless_psrchive_installed
def test_cli_app_does_not_crash_if_archive_cannot_be_processed(
    tmp_path_factory: pytest.TempPathFactory,
    archive_path: Path,
):
    outdir = Path(tmp_path_factory.mktemp("clfd_outdir"))
    args = [
        "--outdir",
        str(outdir),
        str(archive_path),
        "/non/existent/archive.ar",
    ]
    run_program(args)
