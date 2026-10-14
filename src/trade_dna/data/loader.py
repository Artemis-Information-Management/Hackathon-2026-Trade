"""Load the tidy trade data, falling back to the synthetic sample.

The app never reads raw Eurostat files directly. It reads the parquet
produced by ``scripts/prepare_data.py`` (or ``scripts/fetch_data.py``).
If that file is missing, it loads a clearly-labelled synthetic sample so
the UI keeps working while the data pipeline is being built.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..config import TRADE_FILE, TRADE_LU_DETAIL_FILE
from . import sample
from .schema import validate


@dataclass(frozen=True)
class DataStatus:
    is_sample: bool
    source: str
    n_rows: int
    reporters: tuple[str, ...]
    periods: tuple[str, str]


def load_trade() -> tuple[pd.DataFrame, DataStatus]:
    """Annual HS2 trade for all reporters (the main table)."""
    if TRADE_FILE.exists():
        df = validate(pd.read_parquet(TRADE_FILE))
        src = str(TRADE_FILE.relative_to(TRADE_FILE.parents[2]))
        is_sample = False
    else:
        df = sample.make_sample_trade()
        src = "synthetic sample (data/processed/trade_hs2.parquet not found)"
        is_sample = True
    status = DataStatus(
        is_sample=is_sample,
        source=src,
        n_rows=len(df),
        reporters=tuple(sorted(df["reporter"].unique())),
        periods=(df["period"].min(), df["period"].max()),
    )
    return df, status


def load_lu_detail() -> tuple[pd.DataFrame, bool]:
    """Luxembourg detail down to CN8. Returns (df, is_sample)."""
    if TRADE_LU_DETAIL_FILE.exists():
        return validate(pd.read_parquet(TRADE_LU_DETAIL_FILE)), False
    return sample.make_sample_lu_detail(), True


def load_monthly() -> tuple[pd.DataFrame, bool]:
    """Monthly series (for seasonality). Falls back to sample."""
    df, _ = load_trade()
    monthly = df[df["freq"] == "M"]
    if len(monthly):
        return monthly, False
    return sample.make_sample_monthly(), True


def data_status() -> DataStatus:
    return load_trade()[1]
