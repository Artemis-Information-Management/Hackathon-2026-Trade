#!/usr/bin/env python3
"""Pull ds-045409 from the Eurostat Comext API in small, targeted extractions.

The API refuses unfiltered queries (the full dataset is billions of cells),
so we never ask for "everything". Each extraction below is sized to answer
one page of the app and fits in a handful of requests:

  A  eu27_hs2      EU27 reporters x WORLD x HS2        annual 1999-   -> lens 1 (twins)
  B  lu_partners   LU x ALL partners x HS2             annual 1999-   -> lens 2 (dependency)
  C  lu_cn8        LU x WORLD x ALL codes (HS2..CN8)   annual, a few years -> lens 3 (zoom)
  D  lu_monthly    LU x WORLD x HS2                    monthly 2015-  -> lens 4 (R, seasonality)

Usage:
    python scripts/fetch_data.py                # run A, B, C, D
    python scripts/fetch_data.py A D            # only some
    python scripts/fetch_data.py C --years 2024 2019 2014
    python scripts/fetch_data.py B --since 2015

Each extraction is saved as its own CSV in data/raw/api/ (so a crash costs
one file, not everything), then everything is merged into the parquet files
the app reads. Re-running skips extractions whose CSV already exists.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trade_dna.config import DATA_PROCESSED, DATA_RAW, EU27, FOCUS, START_YEAR, TRADE_FILE, TRADE_LU_DETAIL_FILE  # noqa: E402
from trade_dna.data.eurostat import build_query, fetch_json_stat, json_stat_to_frame  # noqa: E402

HS2 = ["TOTAL"] + [f"{i:02d}" for i in range(1, 100)]
RAW_API = DATA_RAW / "api"
PAUSE = 1.0  # seconds between requests, be polite to the server


def _run(name: str, queries: list[tuple[str, list[tuple[str, str]]]], force: bool) -> pd.DataFrame | None:
    out_path = RAW_API / f"{name}.csv"
    if out_path.exists() and not force:
        print(f"[{name}] exists, skipping ({out_path})")
        return pd.read_csv(out_path, dtype=str)
    RAW_API.mkdir(parents=True, exist_ok=True)
    frames = []
    for label, q in queries:
        print(f"[{name}] {label} …", end=" ", flush=True)
        try:
            df = json_stat_to_frame(fetch_json_stat(q))
            frames.append(df)
            print(f"{len(df):,} rows")
        except Exception as e:  # keep going, report at the end
            print(f"FAILED: {e}")
        time.sleep(PAUSE)
    if not frames:
        print(f"[{name}] nothing fetched")
        return None
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(out_path, index=False)
    print(f"[{name}] saved {len(df):,} rows -> {out_path}")
    return df


# --------------------------------------------------------------------------- #
# The four extractions
# --------------------------------------------------------------------------- #


def extraction_A(args) -> list:
    """One request per reporter: TOTAL + 99 HS2 chapters, WORLD, both flows, annual."""
    return [(rep, build_query([rep], ["WORLD"], HS2, since=args.since, freq="A")) for rep in args.reporters]


def extraction_B(args) -> list:
    """One request per year: LU x all partners x HS2, both flows. ~50k cells each."""
    years = range(int(args.since), int(args.until) + 1)
    return [(str(y), build_query([FOCUS], None, HS2, time=str(y), freq="A")) for y in years]


def extraction_C(args) -> list:
    """One request per year: LU x WORLD x every product code (HS2, HS4, HS6, CN8)."""
    return [(str(y), build_query([FOCUS], ["WORLD"], None, time=str(y), freq="A")) for y in args.years]


def extraction_D(args) -> list:
    """One request: LU x WORLD x HS2, monthly since --monthly-since."""
    return [("monthly", build_query([FOCUS], ["WORLD"], HS2, since=args.monthly_since, freq="M"))]


EXTRACTIONS = {"A": ("eu27_hs2", extraction_A), "B": ("lu_partners", extraction_B), "C": ("lu_cn8", extraction_C), "D": ("lu_monthly", extraction_D)}


# --------------------------------------------------------------------------- #


def merge_to_parquet() -> None:
    files = sorted(RAW_API.glob("*.csv"))
    if not files:
        print("No raw API files to merge.")
        return
    df = pd.concat([pd.read_csv(f, dtype={"product": str, "flow": str, "period": str}) for f in files], ignore_index=True)
    df = df.drop_duplicates(subset=["reporter", "partner", "product", "flow", "freq", "period"], keep="last")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    is_hs2 = (df["product"].str.len() <= 2) | (df["product"].str.upper() == "TOTAL")
    hs2 = df[is_hs2]
    hs2.to_parquet(TRADE_FILE, index=False)
    print(f"-> {TRADE_FILE}: {len(hs2):,} rows, reporters {hs2['reporter'].nunique()}, {hs2['period'].min()}–{hs2['period'].max()}")

    detail = df[(~is_hs2) & (df["reporter"] == FOCUS)]
    if len(detail):
        detail.to_parquet(TRADE_LU_DETAIL_FILE, index=False)
        print(f"-> {TRADE_LU_DETAIL_FILE}: {len(detail):,} rows, finest level {detail['product'].str.len().max()} digits, years {sorted(detail['period'].unique())}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("which", nargs="*", default=list(EXTRACTIONS), help="A B C D (default: all)")
    ap.add_argument("--reporters", nargs="+", default=EU27, help="for A")
    ap.add_argument("--since", default=str(START_YEAR), help="first year for A and B")
    ap.add_argument("--until", default=str(time.localtime().tm_year), help="last year for B")
    ap.add_argument("--years", nargs="+", default=["2024", "2019", "2014", "2009", "2004", "1999"], help="years for C")
    ap.add_argument("--monthly-since", default="2015-01", help="first month for D")
    ap.add_argument("--force", action="store_true", help="re-download even if the CSV exists")
    ap.add_argument("--no-merge", action="store_true")
    args = ap.parse_args()

    for key in args.which:
        key = key.upper()
        if key not in EXTRACTIONS:
            sys.exit(f"Unknown extraction {key}; choose from {list(EXTRACTIONS)}")
        name, builder = EXTRACTIONS[key]
        _run(name, builder(args), args.force)

    if not args.no_merge:
        merge_to_parquet()


if __name__ == "__main__":
    main()
