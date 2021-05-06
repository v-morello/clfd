import pytest
import numpy as np

from pathlib import Path


@pytest.fixture(scope="module")
def cube():

    """
    Load the data cube for testing.
    """

    return np.load(
        Path(__file__).parent.joinpath(
            "data",
            "npy_example.npy",
        )
    )
