import importlib
from dataclasses import is_dataclass
from typing import Any

import numpy as np
import pytest

from clfd.serialization import shallow_asdict


def has_module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


skip_unless_psrchive_installed = pytest.mark.skipif(
    not has_module_available("psrchive"),
    reason="psrchive python bindings must be installed",
)


def is_container_like(obj) -> bool:
    return isinstance(obj, (list, tuple, dict)) or is_dataclass(obj)


def ndarray_eq(a: Any, b: Any) -> bool:
    """
    Semi-general equality test that works on ndarrays and containers with
    ndarrays. This function recursively looks into lists, tuples, dicts
    and dataclasses.
    """
    if not is_container_like(a) and not is_container_like(b):
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            return np.array_equal(a, b)
        return a == b

    if not type(a) is type(b):
        return False

    if is_dataclass(a):
        a = shallow_asdict(a)
        b = shallow_asdict(b)

    if isinstance(a, dict):
        return (a.keys() == b.keys()) and all(
            ndarray_eq(x, y) for x, y in zip(a.values(), b.values())
        )

    if isinstance(a, (list, tuple)):
        return (len(a) == len(b)) and all(
            ndarray_eq(x, y) for x, y in zip(a, b)
        )

    raise TypeError(f"Unsupported type: {type(a)}")
