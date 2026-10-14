"""Get Eurostat Comext data (ds-045409) into the tidy schema.

Two routes, pick whichever works fastest on the day:

1. **Bulk CSV** (most reliable): in the Eurostat Data Browser, customise the
   dataset (reporters, partners, HS2 products, flows, years), download as
   CSV, drop the file(s) in ``data/raw/`` and run ``scripts/prepare_data.py``.

2. **API** (``fetch_json_stat``): the Comext dissemination API returns
   JSON-stat 2.0. The endpoint and dimension codes below are the ones used
   for Comext datasets at the time of writing; verify once in a browser
   before relying on it, and keep queries small (one reporter, one year
   range at a time) to avoid time-outs.

Both routes end in ``validate()`` so downstream code sees one schema.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

from ..config import EUROSTAT_DATASET
from .schema import validate

COMEXT_API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data"

# --------------------------------------------------------------------------- #
# Route 2: API
# --------------------------------------------------------------------------- #


def build_query(
    reporters: Iterable[str] | None,
    partners: Iterable[str] | None = ("WORLD",),
    products: Iterable[str] | None = ("TOTAL",),
    flows: Iterable[str] | None = ("1", "2"),
    freq: str = "A",
    since: str | None = None,
    until: str | None = None,
    time: str | None = None,
    indicator: str = "VALUE_IN_EUROS",
) -> list[tuple[str, str]]:
    """Query string as a list of (key, value) pairs.

    Several values for one dimension = the parameter repeated (Eurostat rule).
    Passing ``None`` for a dimension leaves it unfiltered = *all* its values,
    which is how you ask for "all partners" or "all product codes".
    ``time`` selects one period; ``since``/``until`` select a range.
    """
    q: list[tuple[str, str]] = [("format", "JSON"), ("lang", "EN"), ("freq", freq), ("indicators", indicator)]
    for key, values in (("reporter", reporters), ("partner", partners), ("product", products), ("flow", flows)):
        if values is not None:
            q += [(key, v) for v in values]
    if time:
        q.append(("time", time))
    else:
        if since:
            q.append(("sinceTimePeriod", since))
        if until:
            q.append(("untilTimePeriod", until))
    return q


def fetch_json_stat(query: list[tuple[str, str]], dataset: str = EUROSTAT_DATASET, timeout: int = 180, retries: int = 6, wait: int = 20) -> dict:
    """GET the query; if Eurostat answers 'being processed asynchronously', poll until ready."""
    url = f"{COMEXT_API}/{dataset}"
    for attempt in range(retries):
        resp = requests.get(url, params=query, timeout=timeout)
        resp.raise_for_status()
        js = resp.json()
        if "value" in js:
            return js
        # Large extractions are queued; the API asks us to repeat the same request later.
        status = js.get("warning") or js.get("error") or js.get("status") or js
        print(f"  queued by Eurostat ({str(status)[:80]}…), retry {attempt + 1}/{retries} in {wait}s")
        time.sleep(wait)
    raise TimeoutError("Eurostat did not return the extraction in time; split the query further")


def json_stat_to_frame(js: dict) -> pd.DataFrame:
    """Flatten a JSON-stat 2.0 response into one row per observation."""
    dims = js["id"]
    sizes = js["size"]
    categories = []
    for d in dims:
        index = js["dimension"][d]["category"]["index"]
        if isinstance(index, dict):
            codes = sorted(index, key=index.get)
        else:
            codes = list(index)
        categories.append(codes)

    values = js["value"]
    if isinstance(values, dict):
        flat_idx = np.array([int(k) for k in values], dtype=np.int64)
        obs = np.array(list(values.values()), dtype=float)
    else:
        arr = np.array(values, dtype=float)
        flat_idx = np.nonzero(~np.isnan(arr))[0]
        obs = arr[flat_idx]

    unravelled = np.unravel_index(flat_idx, sizes)
    data = {d: np.array(cat, dtype=object)[u] for d, cat, u in zip(dims, categories, unravelled)}
    data["value"] = obs
    df = pd.DataFrame(data)
    return _standardise_columns(df)


# --------------------------------------------------------------------------- #
# Route 1: bulk CSV
# --------------------------------------------------------------------------- #


def read_bulk_csv(path: Path) -> pd.DataFrame:
    """Read a CSV exported from the Data Browser (SDMX-CSV or similar)."""
    df = pd.read_csv(path, dtype=str, low_memory=False)
    return _standardise_columns(df)


def read_all_raw(raw_dir: Path) -> pd.DataFrame:
    frames = [read_bulk_csv(p) for p in sorted(raw_dir.glob("*.csv"))]
    if not frames:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------- #
# Shared
# --------------------------------------------------------------------------- #

_RENAMES = {
    "reporter": "reporter",
    "declarant": "reporter",
    "partner": "partner",
    "product": "product",
    "flow": "flow",
    "freq": "freq",
    "time": "period",
    "time_period": "period",
    "obs_value": "value",
    "value": "value",
}


def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c: _RENAMES[c.lower()] for c in df.columns if c.lower() in _RENAMES}
    df = df.rename(columns=cols)
    if "freq" not in df.columns:
        df["freq"] = np.where(df["period"].astype(str).str.len() > 4, "M", "A")
    df["product"] = df["product"].astype(str).str.strip()
    # Eurostat monthly periods come as "2024-03" or "202403"; normalise to "2024-03"
    per = df["period"].astype(str).str.strip()
    df["period"] = np.where(per.str.len() == 6, per.str[:4] + "-" + per.str[4:], per)
    return validate(df)
