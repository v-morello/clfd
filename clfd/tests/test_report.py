import unittest
import os
import tempfile
import numpy
import clfd

from utils import get_example_data_path

try:
    import tables
    HAS_PYTABLES = True
except ImportError:
    HAS_PYTABLES = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    HAS_MATPLOTLIB = True
except:
    HAS_MATPLOTLIB = False


class TestReport(unittest.TestCase):
    """ Check the Report class """
    def setUp(self):
        # Load test data
        self.npy_data_fname = os.path.join(
            get_example_data_path(), "npy_example.npy")
        self.ndarray = numpy.load(self.npy_data_fname)
        self.cube = clfd.DataCube(self.ndarray, copy=False)
        self.frequencies = numpy.linspace(1181.0, 1581.0, 128)

        self.feature_names = ["std", "ptp", "lfamp"]
        self.qmask = 2.0
        self.features = clfd.featurize(
            self.cube, 
            features=self.feature_names
            )
        
        # Run profile masking
        (self.stats, self.profmask) = clfd.profile_mask(self.features, q=self.qmask)

    def get_report(self):
        return clfd.Report(self.features, self.stats, self.profmask, self.qmask, self.frequencies)

    def test_init(self):
        self.get_report()

    @unittest.skipUnless(HAS_PYTABLES, "")
    def test_save_load(self):
        report = self.get_report()
        with tempfile.NamedTemporaryFile(mode="wb", suffix='.h5') as fobj:
            fname = fobj.name
            report.save(fname)
            r = clfd.Report.load(fname)

        self.assertTrue(numpy.allclose(self.frequencies, r.frequencies))
        self.assertTrue(self.feature_names == r.feature_names)
        self.assertEqual(self.qmask, r.qmask)
        self.assertTrue(numpy.allclose(self.features.values, r.features.values))
        self.assertTrue(numpy.allclose(self.stats.values, r.stats.values))
        self.assertTrue(numpy.array_equal(self.profmask, r.profmask))
        self.assertEqual(clfd.__version__, r.version)

    @unittest.skipUnless(HAS_MATPLOTLIB, "")
    def test_save_corner_plot(self):
        report = self.get_report()
        with tempfile.NamedTemporaryFile(mode="wb", suffix='.png') as fobj:
            fname = fobj.name
            report.corner_plot(to_file=fname)
            plt.close()

    @unittest.skipUnless(HAS_MATPLOTLIB, "")
    def test_save_profile_mask_plot(self):
        report = self.get_report()
        with tempfile.NamedTemporaryFile(mode="wb", suffix='.png', delete=False) as fobj:
            fname = fobj.name
            report.profile_mask_plot(to_file=fname)
            plt.close()


if __name__ == "__main__":
    unittest.main()
