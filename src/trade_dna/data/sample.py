"""Synthetic dataset so the app runs before real data is in place.

Everything here is FAKE. It only mimics the shape of the Eurostat data
(annual HS2 by reporter x partner x flow, plus a small CN8 drill-down for LU
and a monthly series) so that the UI and the indicators can be tested.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import COMPARISON_DEFAULT, START_YEAR
from .schema import validate

PRODUCTS = ["27", "30", "39", "72", "73", "76", "84", "85", "87", "88", "90", "94"]
PARTNERS = ["DE", "FR", "BE", "NL", "IT", "US", "CN", "UK", "CH", "PL"]


def _profile(rng: np.random.Generator, n: int) -> np.ndarray:
    w = rng.dirichlet(np.ones(n) * 0.6)
    return w


def make_sample_trade(
    reporters: list[str] | None = None,
    years: tuple[int, int] = (START_YEAR, 2025),
    seed: int = 42,
) -> pd.DataFrame:
    """Annual HS2 trade for a handful of countries, bilateral by partner."""
    rng = np.random.default_rng(seed)
    reporters = reporters or COMPARISON_DEFAULT
    rows = []
    for rep in reporters:
        scale = 1e9 * (0.3 if rep in {"LU", "MT", "EE"} else 3.0)
        prod_w = _profile(rng, len(PRODUCTS))
        part_w = _profile(rng, len(PARTNERS))
        # LU looks a bit like BE on purpose, to have a "twin" in the demo
        if rep == "LU":
            prod_w = 0.6 * prod_w + 0.4 * np.array([0.03, 0.02, 0.08, 0.22, 0.10, 0.05, 0.15, 0.08, 0.06, 0.02, 0.04, 0.15])
            prod_w /= prod_w.sum()
        # partner mix differs by product: some products depend on one partner
        part_w_by_product = {p: 0.4 * part_w + 0.6 * _profile(rng, len(PARTNERS)) for p in PRODUCTS}
        drift = rng.normal(0, 0.02, size=len(PRODUCTS))
        for i, year in enumerate(range(years[0], years[1] + 1)):
            growth = (1.03 + drift) ** i
            shock = 0.85 if year in (2009, 2020) else 1.0
            for flow in ("1", "2"):
                fscale = scale * (1.1 if flow == "1" else 1.0)
                for p, pw, g in zip(PRODUCTS, prod_w, growth):
                    total = fscale * pw * g * shock * rng.lognormal(0, 0.05)
                    for q, qw in zip(PARTNERS, part_w_by_product[p]):
                        if q == rep:
                            continue
                        rows.append((rep, q, p, flow, "A", str(year), total * qw))
                    rows.append((rep, "WORLD", p, flow, "A", str(year), total))
    return validate(pd.DataFrame(rows, columns=["reporter", "partner", "product", "flow", "freq", "period", "value"]))


def make_sample_lu_detail(year: str = "2024", seed: int = 7) -> pd.DataFrame:
    """A CN8-level drill-down for Luxembourg, one year, exports to WORLD."""
    rng = np.random.default_rng(seed)
    rows = []
    for hs2 in PRODUCTS:
        n4 = rng.integers(2, 5)
        for a in range(n4):
            hs4 = f"{hs2}{rng.integers(1, 99):02d}"
            n6 = rng.integers(1, 4)
            for b in range(n6):
                hs6 = f"{hs4}{rng.integers(1, 99):02d}"
                n8 = rng.integers(1, 4)
                for c in range(n8):
                    cn8 = f"{hs6}{rng.integers(1, 99):02d}"
                    rows.append(("LU", "WORLD", cn8, "2", "A", year, float(rng.pareto(1.5) * 1e6)))
    df = pd.DataFrame(rows, columns=["reporter", "partner", "product", "flow", "freq", "period", "value"])
    df = df.drop_duplicates(subset=["product"])
    return validate(df)


def make_sample_monthly(seed: int = 3) -> pd.DataFrame:
    """Monthly LU exports to WORLD for a few HS2 chapters, with seasonality."""
    rng = np.random.default_rng(seed)
    periods = pd.period_range("2015-01", "2025-12", freq="M")
    rows = []
    for p, amp in (("72", 0.15), ("22", 0.35), ("84", 0.08), ("94", 0.25)):
        base = rng.uniform(3e7, 2e8)
        for i, per in enumerate(periods):
            trend = base * (1 + 0.004 * i)
            season = 1 + amp * np.sin(2 * np.pi * (per.month - 1) / 12 + rng.uniform(0, 0.3))
            august = 0.75 if per.month == 8 else 1.0
            rows.append(("LU", "WORLD", p, "2", "M", str(per), trend * season * august * rng.lognormal(0, 0.04)))
    return validate(pd.DataFrame(rows, columns=["reporter", "partner", "product", "flow", "freq", "period", "value"]))
