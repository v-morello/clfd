import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from clfd import __version__
from clfd.profile_masking import ProfileMaskingResult
from clfd.serialization import JSONSerializableDataclass, json_dump, json_load
from clfd.spike_finding import SpikeFindingResult


@dataclass(frozen=True)
class Report(JSONSerializableDataclass):
    """
    The intermediate and final results of the whole data cleaning process.
    """

    profile_masking_result: ProfileMaskingResult
    spike_finding_result: Optional[SpikeFindingResult] = None
    archive_path: Optional[str] = None
    version: str = __version__

    def __post_init__(self):
        object.__setattr__(
            self, "archive_path", str(Path(self.archive_path).resolve())
        )

    def plot(self):
        """
        Plot the report, returning a matplotlib Figure.
        """
        from clfd.report_plotting import plot_report

        return plot_report(self)

    def save(self, path: Union[str, os.PathLike]):
        """
        Save to file in JSON format.
        """
        with open(path, "w") as file:
            json_dump(self, file, indent=4)

    @classmethod
    def load(cls, path: Union[str, os.PathLike]) -> "Report":
        """
        Load from file in JSON format.
        """
        with open(path, "r") as file:
            return json_load(file)
