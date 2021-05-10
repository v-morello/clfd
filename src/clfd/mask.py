import numpy as np
import pandas as pd
import scipy.stats as st

from typing import (
    List,
    Dict,
    Tuple,
    Optional,
    Iterable,
    Callable,
)


def inf_var(var: np.ndarray):
    var[var == 0] = np.inf
    return var


profile_features: Dict[str, Callable] = {
    "std": lambda x: x.std(axis=-1, dtype=np.float64),
    "var": lambda x: x.var(axis=-1, dtype=np.float64),
    "ptp": lambda x: x.ptp(axis=-1),
    "lfamp": lambda x: abs(np.fft.rfft(x.data, axis=-1)[:, :, 1]),
    "skew": lambda x: st.skew(x.astype(np.float64), axis=-1),
    "kurtosis": lambda x: st.kurtosis(x.astype(np.float64), axis=-1),
    "acf": lambda x: np.mean(
        x[..., :-1] * x[..., 1:],
        dtype=np.float64,
        axis=-1,
    )
    / inf_var(x.var(axis=-1, dtype=np.float64)),
}


def featurize(
    data: np.ndarray,
    features: Iterable,
) -> pd.DataFrame:

    """"""

    feats: Dict = {}

    for name in features:
        feature = profile_features.get(name, None)
        if not feature:
            raise ValueError(
                """
                No such feature, {:s}, has been implemented in clfd.
                Exiting...
                """.format(
                    feature
                )
                .replace("\n", "")
                .strip()
            )
        index = pd.MultiIndex.from_product(
            [range(data.shape[0]), range(data.shape[1])],
            names=["subint", "channel"],
        )
        feats[name] = feature(data).ravel()

    return pd.DataFrame(feats, index=index)


def statistics(
    features: pd.DataFrame,
    Q: float = 2.0,
) -> pd.DataFrame:

    """"""

    stats = features.quantile([0.25, 0.50, 0.75])
    stats = stats.rename(
        {
            0.25: "q1",
            0.50: "med",
            0.75: "q3",
        }
    )

    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - (Q * stats.loc["iqr"])
    stats.loc["vmax"] = stats.loc["q3"] + (Q * stats.loc["iqr"])

    return stats


def profile_mask(
    features: pd.DataFrame,
    Q: float = 2.0,
    zapchans: Optional[List] = None,
) -> Tuple[pd.DataFrame, np.ndarray]:

    """"""

    zap = (zapchans is not None) and (len(zapchans) > 0)
    if zap:
        stats = statistics(
            features.drop(
                zapchans,
                level=1,
            ),
            Q,
        )
    else:
        stats = statistics(features, Q)

    mask = (
        ((features > stats.loc["vmax"]) | (features < stats.loc["vmin"]))
        .sum(axis=1)
        .values.astype(bool)
        .reshape(features.index.levshape)
    )
    if zap:
        mask[:, zapchans] = True

    return stats, mask


def time_phz_mask(
    data: np.ndarray,
    Q: float = 4.0,
    zapchans: Optional[List] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

    """"""

    chanmask = np.ones(data.shape[1], dtype=bool)

    zap = (zapchans is not None) and (len(zapchans) > 0)
    if zap:
        chanmask[zapchans] = False

    valid_chans = np.where(chanmask)[0]
    num_valids = valid_chans.sum()

    scrunch = data[:, valid_chans].sum(axis=1)

    stats = pd.DataFrame(
        np.percentile(
            scrunch,
            [25, 50, 75],
            axis=0,
        )
    ).rename({0: "q1", 1: "med", 2: "q3"})

    stats.loc["iqr"] = stats.loc["q3"] - stats.loc["q1"]
    stats.loc["vmin"] = stats.loc["q1"] - (Q * stats.loc["iqr"])
    stats.loc["vmax"] = stats.loc["q3"] + (Q * stats.loc["iqr"])

    upper = scrunch < stats.loc["vmin"].values
    lower = scrunch > stats.loc["vmax"].values
    mask = (upper) | (lower)

    med = stats.loc["med"].values

    nsubs, nchans, _ = data.shape
    new_values = (
        med / num_valids
        + np.median(
            data,
            axis=2,
        ).reshape(nsubs, nchans, 1)
    )

    return mask, valid_chans, new_values