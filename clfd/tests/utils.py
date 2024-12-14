import importlib
import os


def get_example_data_path():
    cdir, __ = os.path.split(__file__)
    return os.path.realpath(os.path.join(cdir, "..", "example_data"))


def has_module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


HAS_PSRCHIVE = has_module_available("psrchive")
HAS_MATPLOTLIB = has_module_available("matplotlib.pyplot")
HAS_PYTABLES = has_module_available("tables")
