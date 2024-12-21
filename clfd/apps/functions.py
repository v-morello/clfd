import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

import matplotlib.pyplot as plt

from clfd import ArchiveHandler, Report, find_time_phase_spikes, profile_mask


def load_zapfile(fname: Union[str, os.PathLike]) -> list[int]:
    """
    Load zapfile into a list of channel indices.
    """
    with open(fname, "r") as file:
        zap_channels = list(map(int, file.read().strip().split()))
    return zap_channels


def process_file(
    path: Union[str, os.PathLike],
    zap_channels: list[int],
    outdir: Optional[Union[str, os.PathLike]] = None,
    features: Sequence[str] = ("std", "ptp", "lfamp"),
    qmask: float = 2.0,
    despike: bool = False,
    qspike: float = 4.0,
    save_report: bool = False,
) -> Path:
    """
    Process a single archive file end to end. Returns the path to the output
    archive.
    """
    path = Path(path).resolve()
    handler = ArchiveHandler(path)
    cube = handler.data_cube()
    pm_result = profile_mask(
        cube, features=features, q=qmask, zap_channels=zap_channels
    )
    handler.apply_profile_mask(pm_result.mask)

    if despike:
        sf_result, plan = find_time_phase_spikes(
            cube, q=qspike, zap_channels=zap_channels
        )
        handler.apply_spike_subtraction_plan(plan)
    else:
        sf_result = None

    outdir = Path(outdir).resolve() if outdir else path.parent
    output_path = outdir / (path.name + ".clfd")
    handler.save(output_path)

    if save_report:
        report = Report(
            profile_masking_result=pm_result,
            spike_finding_result=sf_result,
            archive_path=path,
        )
        report_path = outdir / (path.stem + "_clfd_report.json")
        report.save(report_path)

        plot_path = report_path.with_suffix(".png")
        plt.switch_backend("Agg")
        report.plot().savefig(plot_path)

    return output_path


@dataclass
class WorkerResult:
    input_path: Path
    output_path: Optional[Path] = None
    traceback: Optional[str] = None


class Worker:
    """
    Callable applied by a process Pool.
    """

    def __init__(self, kwargs: dict):
        self.kwargs = kwargs

    def __call__(self, path: Path) -> WorkerResult:
        kwargs = self.kwargs | {"path": path}
        try:
            output_path = process_file(**kwargs)
            return WorkerResult(path, output_path, None)
        except Exception:
            return WorkerResult(path, None, traceback.format_exc())
