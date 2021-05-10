from .core import Cube

from .mask import (
    featurize,
    statistics,
    profile_mask,
    time_phz_mask,
    profile_features,
)

from .report import Report


__all__ = [
    "Cube",
    "Report",
    "featurize",
    "statistics",
    "profile_mask",
    "time_phz_mask",
    "profile_features",
]

from ._version import get_versions  # type: ignore

__version__ = get_versions()["version"]
del get_versions