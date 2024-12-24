import subprocess
from pathlib import Path

import pytest
from numpy.typing import NDArray

from .utils import HAS_PSRCHIVE


def test_cli_app_entrypoint_exists():
    """
    Self-explanatory.
    """
    exit_code = subprocess.check_call(["clfd", "--help"])
    assert exit_code == 0


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
    assert expected_archive_path.exists()

    # FIXME: disabled until refactoring is finished
    # expected_report_path = outdir / "psrchive_example_clfd_report.h5"
    # assert expected_report_path.exists()

    # report = Report.load(expected_report_path)
    # assert np.array_equal(report.profmask, expected_profmask)
    # assert np.array_equal(report.tpmask, expected_tpmask)
