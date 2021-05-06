import numpy as np
import pandas as pd
import scipy.stats as st

from typing import (
    List,
    Dict,
    Optional,
    Iterable,
)


def inf_var(var: np.ndarray):
    var[var == 0] = np.inf
    return var


pf = {
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


def baselines(cube: np.ndarray):

    """"""

    nsub, nchan, _ = cube.shape
    baselines = np.median(cube, axis=2)
    cube = cube - baselines.reshape(nsub, nchan, 1)
    return baselines, cube


def featurize(
    cube: np.ndarray,
    features: Iterable = (
        "std",
        "ptp",
        "lfamp",
    ),
) -> pd.DataFrame:

    """"""

    data: Dict = {}

    for name in features:
        feature = pf.get(name, None)
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
            [range(cube.shape[0]), range(cube.shape[1])],
            names=["subint", "channel"],
        )
        data[name] = feature(cube).ravel()
    feats = pd.DataFrame(data, index=index)
    return feats


def statistics(
    features: pd.DataFrame,
    Q: float = 2.0,
):

    """"""

    stats = features.quantile([0.25, 0.50, 0.75])
    stats = stats.rename(
        {
            0.25: "Q1",
            0.50: "Q2",
            0.75: "Q3",
        }
    )

    stats.loc["IQR"] = stats.loc["Q3"] - stats.loc["Q1"]
    stats.loc["VMIN"] = stats.loc["Q1"] - (Q * stats.loc["IQR"])
    stats.loc["VMAX"] = stats.loc["Q3"] + (Q * stats.loc["IQR"])

    return stats


def mask_profile(
    cube: np.ndarray,
    features: pd.DataFrame,
    Q: float = 2.0,
    zapchans: Optional[List] = None,
):

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
        ((features > stats.loc["VMAX"]) | (features < stats.loc["VMIN"]))
        .sum(axis=1)
        .values.astype(bool)
        .reshape(features.index.levshape)
    )
    if zap:
        mask[:, zapchans] = True

    for (
        isub,
        ichan,
    ) in np.vstack(np.where(mask)).T:
        cube[isub, ichan, :] = 0

    return stats, mask


def mask_time_phz(
    cube: np.ndarray,
    Q: float = 4.0,
    zapchans: Optional[List] = None,
):

    """"""

    (
        nsub,
        nchan,
        _,
    ) = cube.shape

    chanmask = np.ones(nchan, dtype=bool)

    zap = (zapchans is not None) and (len(zapchans) > 0)
    if zap:
        chanmask[zapchans] = False

    vchans = np.where(chanmask)[0]
    nvchan = vchans.sum()

    data = cube[:, vchans].sum(axis=1)

    stats = pd.DataFrame(
        np.percentile(
            data,
            [25, 50, 75],
            axis=0,
        )
    ).rename({0: "Q1", 1: "MED", 2: "Q3"})

    stats.loc["IQR"] = stats.loc["Q3"] - stats.loc["Q1"]
    stats.loc["VMIN"] = stats.loc["Q1"] - (Q * stats.loc["IQR"])
    stats.loc["VMAX"] = stats.loc["Q3"] + (Q * stats.loc["IQR"])

    upper = data < stats.loc["VMIN"].values
    lower = data > stats.loc["VMAX"].values

    mask = (upper) | (lower)
    bads = [np.where(row)[0] for row in mask]
    bads = [bad for bad in bads if bad]

    med = stats.loc["MED"].values

    vnew = med / nvchan + baselines(cube)[0].reshape(nsub, nchan, 1)

    for ix, bad in enumerate(bads):
        for vchan in vchans:
            cube[ix, vchan, :][bad] = vnew[ix, vchan, bad]

    return mask, vchans, vnew