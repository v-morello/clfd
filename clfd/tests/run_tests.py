import unittest
import os

def test():
    """ Run all unit tests """
    loader = unittest.TestLoader()
    # NOTE: assume that all unit tests are to be found in the same directory
    # as this file
    suite = loader.discover(os.path.dirname(__file__))
    runner = unittest.TextTestRunner()
    runner.run(suite)