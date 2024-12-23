import os
import tempfile
import unittest

import numpy

import clfd

from .utils import HAS_PSRCHIVE, get_example_data_path


class TestDataCube(unittest.TestCase):
    """Check the DataCube class methods."""

    def setUp(self):
        self.npy_data_fname = os.path.join(get_example_data_path(), "npy_example.npy")
        self.psrchive_data_fname = os.path.join(get_example_data_path(), "psrchive_example.ar")
        self.ndarray = numpy.load(self.npy_data_fname)

    def test_init(self):
        cube = clfd.DataCube(self.ndarray)
        self.assertTrue(numpy.array_equal(cube.orig_data, self.ndarray))

    def test_input_type_errors(self):
        # Input must be numpy.ndarray
        with self.assertRaises(ValueError):
            clfd.DataCube(list(self.ndarray))

    def test_input_dim_errors(self):
        with self.assertRaises(ValueError, msg="Input has less than 3 dimensions"):
            clfd.DataCube(self.ndarray.ravel())

        shape = self.ndarray.shape
        shape4 = tuple(list(shape) + [1])
        with self.assertRaises(ValueError, msg="Input has more than 3 dimensions"):
            clfd.DataCube(self.ndarray.reshape(shape4))

        with self.assertRaises(ValueError, msg="Input has only 1 phase bin"):
            clfd.DataCube(self.ndarray[:, :, :1])

        with self.assertRaises(ValueError, msg="Input has only 1 profile"):
            clfd.DataCube(self.ndarray[:1, :1, :])

    def test_load_save_npy(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".npy") as fobj:
            fname = fobj.name

            # NOTE: leaving self.ndarray untouched
            cube1 = clfd.DataCube(self.ndarray)
            cube1.save_npy(fname)
            cube2 = clfd.DataCube.from_npy(fname)

            self.assertTrue(numpy.array_equal(cube1.orig_data, cube2.orig_data))

    @unittest.skipUnless(HAS_PSRCHIVE, "psrchive python bindings must be installed")
    def test_load_psrchive(self):
        clfd.DataCube.from_psrchive(self.psrchive_data_fname)


if __name__ == "__main__":
    unittest.main()
