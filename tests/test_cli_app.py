import subprocess
from pathlib import Path

import pytest

from .utils import HAS_PSRCHIVE


def test_cli_app_entrypoint_exists():
    """
    Self-explanatory.
    """
    exit_code = subprocess.check_call(["clfd", "--help"])
    assert exit_code == 0


@pytest.mark.skipif(not HAS_PSRCHIVE, reason="psrchive python bindings must be installed")
def test_cli_app(tmp_path_factory: pytest.TempPathFactory):
    """
    Basic end-to-end test of the CLI app on a PSRCHIVE archive.
    """
    archive_path = Path(__file__).parent / ".." / "example_data" / "psrchive_example.ar"
    outdir = Path(tmp_path_factory.mktemp("clfd_outdir"))

    args = ["clfd", str(archive_path), "--despike", "--outdir", str(outdir)]
    subprocess.check_call(args)

    expected_output_archive = outdir / "psrchive_example.ar.clfd"
    expected_output_report = outdir / "psrchive_example_clfd_report.h5"
    assert expected_output_archive.exists()
    assert expected_output_report.exists()
