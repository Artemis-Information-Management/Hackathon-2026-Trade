"""The one tidy schema every module agrees on.

Every data source (Eurostat API, bulk CSV, synthetic sample, R outputs)
is normalised into this shape before anything else touches it.

    reporter : str   ISO2 country code of the declaring country (e.g. "LU")
    partner  : str   ISO2 code of the partner, or an aggregate (e.g. "WORLD")
    product  : str   HS/CN code as a string, zero-padded ("72", "7208", "72081000")
    flow     : str   "1" = imports, "2" = exports
    freq     : str   "A" = annual, "M" = monthly
    period   : str   "2024" for annual, "2024-03" for monthly
    value    : float value in euros
"""

from __future__ import annotations

import pandas as pd

COLUMNS = ["reporter", "partner", "product", "flow", "freq", "period", "value"]


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types and column order; raise if a column is missing."""
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Trade frame is missing columns: {missing}")
    out = df[COLUMNS].copy()
    for c in ["reporter", "partner", "product", "flow", "freq", "period"]:
        out[c] = out[c].astype(str).str.strip()
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["value"])
    return out.reset_index(drop=True)


def product_level(code: str) -> int:
    """HS2 -> 2, HS4 -> 4, HS6 -> 6, CN8 -> 8. 'TOTAL' -> 0."""
    return 0 if code.upper() == "TOTAL" else len(code)
