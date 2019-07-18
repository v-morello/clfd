import os

def get_example_data_path():
    cdir, __ = os.path.split(__file__)
    return os.path.realpath(os.path.join(cdir, '..', 'example_data'))