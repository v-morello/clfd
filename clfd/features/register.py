from typing import Callable

AVAILABLE_FEATURES: dict[str, Callable] = {}


def register_feature(func: Callable):
    """
    Register feature function for use in profile masking.
    """
    if func.__name__ in AVAILABLE_FEATURES:
        raise ValueError(f"A feature named {func.__name__!r} already exists")
    AVAILABLE_FEATURES[func.__name__] = func


def available_features() -> dict[str, Callable]:
    """
    Returns a dictionary {name: func} of available feature functions.
    """
    return dict(AVAILABLE_FEATURES)


def get_feature(name: str) -> Callable:
    """
    Get feature function with given name.
    """
    func = AVAILABLE_FEATURES.get(name, None)
    if func is None:
        raise KeyError(f"No feature named {name!r}")
    return func
