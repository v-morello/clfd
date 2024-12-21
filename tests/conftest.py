from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from clfd import ArchiveHandler


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


@pytest.fixture(scope="module")
def data_cube() -> NDArray:
    """
    Data cube loaded from the example npy file.
    """
    path = Path(__file__).parent / ".." / "example_data" / "npy_example.npy"
    return np.load(path)


@pytest.fixture(scope="module")
def expected_profmask() -> NDArray:
    """
    Expected profile mask when running clfd on the test archive with:
    - features: (std, ptp, lfamp)
    - qmask: 2.0
    Has shape (num_subints, num_channels).
    """
    return two_dimensional_boolean_mask_from_file(
        Path(__file__).parent / "expected_profmask.txt"
    )


@pytest.fixture(scope="module")
def expected_tpmask() -> NDArray:
    """
    Expected time-phase mask when running clfd on the test archive with
    qspike = 2.0. Has shape (num_subints, num_phase_bins).
    """
    return two_dimensional_boolean_mask_from_file(
        Path(__file__).parent / "expected_tpmask.txt"
    )


@pytest.fixture(scope="module")
def archive_path() -> Path:
    return (
        Path(__file__).parent / ".." / "example_data" / "psrchive_example.ar"
    )


@pytest.fixture(scope="module")
def archive_handler(archive_path: Path) -> ArchiveHandler:
    return ArchiveHandler(archive_path)
