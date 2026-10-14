#!/usr/bin/env python3
"""Turn Eurostat CSV exports in data/raw/ into the tidy parquet files the app reads.

Usage:
    python scripts/prepare_data.py

Expects one or more CSV files exported from the Eurostat Data Browser
(dataset ds-045409) in data/raw/. Writes:

    data/processed/trade_hs2.parquet     all reporters, HS2 level (+ TOTAL), annual and/or monthly
    data/processed/trade_lu_cn8.parquet  Luxembourg only, codes longer than 2 digits (HS4/HS6/CN8)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trade_dna.config import DATA_PROCESSED, DATA_RAW, FOCUS, START_YEAR, TRADE_FILE, TRADE_LU_DETAIL_FILE  # noqa: E402
from trade_dna.data.eurostat import read_all_raw  # noqa: E402


def main() -> None:
    df = read_all_raw(DATA_RAW)
    print(f"Read {len(df):,} rows from {DATA_RAW}")

    df = df[df["period"].str[:4].astype(int) >= START_YEAR]
    level = df["product"].str.len()
    is_hs2 = (level <= 2) | (df["product"].str.upper() == "TOTAL")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    hs2 = df[is_hs2]
    hs2.to_parquet(TRADE_FILE, index=False)
    print(f"Wrote {TRADE_FILE} ({len(hs2):,} rows, reporters: {sorted(hs2['reporter'].unique())})")

    detail = df[(~is_hs2) & (df["reporter"] == FOCUS)]
    if len(detail):
        detail.to_parquet(TRADE_LU_DETAIL_FILE, index=False)
        print(f"Wrote {TRADE_LU_DETAIL_FILE} ({len(detail):,} rows, finest level: {detail['product'].str.len().max()} digits)")
    else:
        print("No sub-HS2 rows for LU found; the Smart zoom page will keep using the sample.")


if __name__ == "__main__":
    main()
