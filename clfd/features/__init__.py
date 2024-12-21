from .functions import acf, kurtosis, lfamp, ptp, skew, std, var
from .register import available_features, get_feature, register_feature

for func in (acf, kurtosis, lfamp, ptp, skew, std, var):
    register_feature(func)


__all__ = [
    "available_features",
    "get_feature",
    "register_feature",
]

__all__.extend(list(available_features().keys()))
