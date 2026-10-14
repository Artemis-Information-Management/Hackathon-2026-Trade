"""Run the team's R scripts from Python, exchanging CSV files.

Why files and not rpy2: no fragile binary install, R and Python can be
developed independently, and the outputs can be committed so the app still
works on a machine without R (the jury's laptop, for instance).

Contract (see r/README.md):
    Rscript r/<script>.R --input <in.csv> --output <out.csv> [extra args]

Python writes ``in.csv`` in the tidy schema, R writes ``out.csv``, Python
reads it back. If R is not installed, ``run_or_cached`` returns the last
output committed under data/processed/r/ instead of failing.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pandas as pd

from .config import DATA_PROCESSED, R_DIR

R_OUTPUT_DIR = DATA_PROCESSED / "r"


class RNotAvailable(RuntimeError):
    pass


def rscript_path() -> str | None:
    return shutil.which("Rscript")


def rscript_available() -> bool:
    return rscript_path() is not None


def run_r(script: str, df_in: pd.DataFrame, output_name: str, extra_args: list[str] | None = None, timeout: int = 600) -> pd.DataFrame:
    """Write df_in to CSV, run r/<script>, read the CSV it produces."""
    exe = rscript_path()
    if exe is None:
        raise RNotAvailable("Rscript not found on PATH")
    script_path = R_DIR / script
    if not script_path.exists():
        raise FileNotFoundError(script_path)

    R_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    in_path = R_OUTPUT_DIR / f"_input_{output_name}"
    out_path = R_OUTPUT_DIR / output_name
    df_in.to_csv(in_path, index=False)

    cmd = [exe, str(script_path), "--input", str(in_path), "--output", str(out_path), *(extra_args or [])]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=R_DIR.parent)
    if proc.returncode != 0:
        raise RuntimeError(f"R script failed ({proc.returncode}):\n{proc.stderr[-2000:]}")
    if not out_path.exists():
        raise RuntimeError(f"R script finished but did not write {out_path}")
    return pd.read_csv(out_path)


def cached_output(output_name: str) -> pd.DataFrame | None:
    p = R_OUTPUT_DIR / output_name
    return pd.read_csv(p) if p.exists() else None


def run_or_cached(script: str, df_in: pd.DataFrame, output_name: str, extra_args: list[str] | None = None, force: bool = False) -> tuple[pd.DataFrame, str]:
    """Return (result, source) where source is 'r' or 'cache'."""
    if not force:
        cached = cached_output(output_name)
        if cached is not None:
            return cached, "cache"
    if rscript_available():
        return run_r(script, df_in, output_name, extra_args), "r"
    cached = cached_output(output_name)
    if cached is not None:
        return cached, "cache"
    raise RNotAvailable("Rscript is not installed and no cached output exists under data/processed/r/")


def list_r_scripts() -> list[Path]:
    return sorted(R_DIR.glob("*.R"))
