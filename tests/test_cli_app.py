import subprocess
from pathlib import Path

import pytest

from .utils import HAS_PSRCHIVE
from clfd import Report

import numpy as np
from numpy.typing import NDArray


def test_cli_app_entrypoint_exists():
    """
    Self-explanatory.
    """
    exit_code = subprocess.check_call(["clfd", "--help"])
    assert exit_code == 0


def two_dimensional_boolean_mask_from_text(text: str) -> NDArray:
    """
    Self-explanatory.
    """
    result = []
    for row_text in text.strip().split("\n"):
        row = list(map(int, row_text))
        result.append(row)
    return np.asarray(result, dtype=bool)


def two_dimensional_boolean_mask_from_file(path: Path) -> NDArray:
    """
    Self-explanatory.
    """
    with open(path, "r") as file:
        return two_dimensional_boolean_mask_from_text(file.read())


@pytest.fixture(name="expected_profmask")
def fixture_expected_profmask() -> NDArray:
    """
    Expected profile mask when running clfd on the test archive with:
    - features: (std, ptp, lfamp)
    - qmask: 2.0
    Has shape (num_subints, num_channels).
    """
    return two_dimensional_boolean_mask_from_file(Path(__file__).parent / "expected_profmask.txt")


@pytest.fixture(name="expected_tpmask")
def fixture_expected_tpmask() -> NDArray:
    """
    Expected time-phase mask when running clfd on the test archive with
    qspike = 2.0. Has shape (num_subints, num_phase_bins).
    """
    return two_dimensional_boolean_mask_from_file(Path(__file__).parent / "expected_tpmask.txt")


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_cli_app(
    tmp_path_factory: pytest.TempPathFactory, expected_profmask: NDArray, expected_tpmask: NDArray
):
    """
    Basic end-to-end test of the CLI app on a PSRCHIVE archive.
    """
    archive_path = Path(__file__).parent / ".." / "example_data" / "psrchive_example.ar"
    outdir = Path(tmp_path_factory.mktemp("clfd_outdir"))

    args = ["clfd", str(archive_path), "--despike", "--qspike", str(2.0), "--outdir", str(outdir)]
    subprocess.check_call(args)

    expected_archive_path = outdir / "psrchive_example.ar.clfd"
    expected_report_path = outdir / "psrchive_example_clfd_report.h5"
    assert expected_archive_path.exists()
    assert expected_report_path.exists()

    report = Report.load(expected_report_path)
    assert np.array_equal(report.profmask, expected_profmask)
    assert np.array_equal(report.tpmask, expected_tpmask)
