import attr
import numpy as np

from pathlib import Path
from priwo import read_pfd, write_pfd
from typing import Dict, List, Iterable, Optional

from .mask import (
    featurize,
    profile_mask,
    time_phz_mask,
    profile_features,
)

from .report import Report


@attr.s(repr=False, auto_attribs=True)
class Cube(object):

    """"""

    data: np.ndarray

    fname: Optional[str] = None
    finfo: Optional[Dict] = None

    def __str__(self):
        return "\n".join(
            [
                f"{type(self).__name__}",
                "========================================",
                f"Number of sub-integrations: {self.nsub}",
                f"Number of (sub-)channels: {self.nchan}",
                f"Number of bins in each profile: {self.nbin}",
                f"Name of data file: {self.fname}",
                f"Cleaned? {(lambda: 'Yes' if hasattr(self, '_cleaned') else 'No')()}",
            ]
        )

    def __repr__(self):
        return str(self)

    @property
    def original(self):

        """"""

        return self.data + self.baselines.reshape(
            self.nsub,
            self.nchan,
            1,
        )

    @property
    def cleaned(self) -> Optional[np.ndarray]:

        """"""

        return getattr(self, "_cleaned", None)

    @property
    def nsub(self):

        """"""

        return self.data.shape[0]

    @property
    def nchan(self):

        """"""

        return self.data.shape[1]

    @property
    def nbin(self):

        """"""

        return self.data.shape[2]

    def subtract_baselines(self):

        """"""

        self.baselines = np.median(self.data, axis=2)
        self.data = self.data - self.baselines.reshape(
            self.nsub,
            self.nchan,
            1,
        )

    def mask_profiles(
        self,
        Q: float = 2.0,
        dynamic: Optional[str] = None,
        zapchans: Optional[List] = None,
        features: Iterable = profile_features.keys(),
    ):

        """"""

        self.Q = Q

        self.zapchans: Dict = {}
        self.zapchans["profile_mask"] = zapchans

        self._cleaned = self.original.copy()

        if dynamic is not None:
            try:
                features = {
                    "low": ("std", "ptp", "lfamp"),
                    "high": ("skew", "kurtosis", "acf"),
                }[dynamic]
            except KeyError:
                raise ValueError(
                    f"Wrong value ({dynamic}) specified for the dynamic option. Cannot featurize. Exiting..."
                )

        self.feats = featurize(self.data, features=features)
        self.stats, self.profile_mask = profile_mask(self.feats, Q=Q, zapchans=zapchans)

        for (isub, ichan) in np.vstack(np.where(self.profile_mask)).T:
            self._cleaned[isub, ichan, :] = 0

    def mask_time_phz(
        self,
        Q_spike: float = 4.0,
        zapchans: Optional[List] = None,
    ) -> None:

        """"""

        self.Q_spike = Q_spike

        if not hasattr(self, "_cleaned"):
            self._cleaned = self.original.copy()

        if not hasattr(self, "zapchans"):
            self.zapchans = {}

        self.zapchans["time_phz_mask"] = zapchans

        self.time_phz_mask, valid_chans, new_vals = time_phz_mask(
            self.data,
            Q=Q_spike,
            zapchans=zapchans,
        )
        bads = [np.where(row)[0] for row in self.time_phz_mask]
        bads = [bad for bad in bads if bad]

        for ix, bad in enumerate(bads):
            for valid_chan in valid_chans:
                self._cleaned[ix, valid_chan, :][bad] = new_vals[ix, valid_chan, bad]

    def make_report(self):

        """"""

        try:
            return Report(
                filename=self.fname,
                Q=self.Q,
                feats=self.feats,
                stats=self.stats,
                profile_mask=self.profile_mask,
                Q_spike=getattr(self, "Q_spike", None),
                zapchans=getattr(self, "zapchans", None),
                time_phz_mask=getattr(self, "time_phz_mask", None),
            )
        except:
            raise ValueError(
                "Could not make a report. Maybe you haven't cleaned the cube yet? Exiting..."
            )

    @classmethod
    def from_npy(
        cls,
        fname: str,
    ):

        """"""

        fname = str(Path(fname).resolve())
        cube = cls(np.load(fname))
        cube.subtract_baselines()
        return cube

    @classmethod
    def from_pfd(
        cls,
        fname: str,
    ):

        """"""

        fname = str(Path(fname).resolve())
        finfo = read_pfd(fname)
        data = finfo.pop("profs")
        cube = cls(
            data,
            fname=fname,
            finfo=finfo,
        )
        cube.subtract_baselines()
        return cube

    def to_npy(
        self,
        fname: Optional[str] = None,
        dtype: type = np.float32,
    ):

        """"""

        if fname is None:
            fname = self.fname

        np.save(
            fname,
            self.original.astype(dtype),
        )

    def to_pfd(
        self,
        fname: Optional[str] = None,
        dtype: type = np.float32,
    ):

        """"""

        if fname is None:
            fname = self.fname

        if self.finfo is not None:
            self.finfo["profs"] = self.original.astype(dtype)
            write_pfd(self.finfo, fname)
        else:
            raise IOError("There is no metadata. Cannot write the cube to a PFD file.")