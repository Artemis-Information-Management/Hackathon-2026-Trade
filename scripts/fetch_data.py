#!/usr/bin/env python3
"""Pull ds-045409 from the Eurostat Comext API into data/processed/trade_hs2.parquet.

Usage:
    python scripts/fetch_data.py                 # EU27 reporters, HS2 x WORLD, annual, since 1999
    python scripts/fetch_data.py --reporters LU BE NL --since 2015
    python scripts/fetch_data.py --partners WORLD DE FR BE NL US CN   # bilateral (needed for lens 2)

One request per reporter keeps each call small. If the API is slow or down
on the day, use the Data Browser export + scripts/prepare_data.py instead.
Verify the endpoint once in a browser before trusting it (see data/eurostat.py).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trade_dna.config import DATA_PROCESSED, EU27, START_YEAR, TRADE_FILE  # noqa: E402
from trade_dna.data.eurostat import build_query, fetch_json_stat, json_stat_to_frame  # noqa: E402

HS2 = [f"{i:02d}" for i in range(1, 100)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reporters", nargs="+", default=EU27)
    ap.add_argument("--partners", nargs="+", default=["WORLD"])
    ap.add_argument("--products", nargs="+", default=["TOTAL", *HS2])
    ap.add_argument("--freq", default="A", choices=["A", "M"])
    ap.add_argument("--since", default=str(START_YEAR))
    ap.add_argument("--out", default=str(TRADE_FILE))
    args = ap.parse_args()

    frames = []
    for rep in args.reporters:
        q = build_query([rep], args.partners, args.products, freq=args.freq, since=args.since)
        print(f"{rep}: fetching…", end=" ", flush=True)
        try:
            js = fetch_json_stat(q)
            df = json_stat_to_frame(js)
            frames.append(df)
            print(f"{len(df):,} rows")
        except Exception as e:  # keep going, report at the end
            print(f"FAILED ({e})")
        time.sleep(0.5)

    if not frames:
        sys.exit("Nothing fetched.")
    out = pd.concat(frames, ignore_index=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    if Path(args.out).exists():
        prev = pd.read_parquet(args.out)
        out = pd.concat([prev, out]).drop_duplicates(subset=["reporter", "partner", "product", "flow", "freq", "period"], keep="last")
    out.to_parquet(args.out, index=False)
    print(f"Wrote {args.out}: {len(out):,} rows, {out['reporter'].nunique()} reporters, {out['period'].min()}–{out['period'].max()}")
    DATA_PROCESSED.mkdir(exist_ok=True)


if __name__ == "__main__":
    main()
