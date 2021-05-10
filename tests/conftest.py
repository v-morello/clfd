import pytest

from clfd import Cube
from pathlib import Path


@pytest.fixture(scope="module")
def cube():

    """
    Load the data cube for testing.
    """

    return Cube.from_npy(
        Path(__file__)
        .parent.resolve()
        .joinpath(
            "data",
            "npy_example.npy",
        )
    )