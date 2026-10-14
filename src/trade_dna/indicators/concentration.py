"""Lens 2 - Dependency points: where does Luxembourg rely on one partner?

Herfindahl-Hirschman index of partner concentration, per product:

    HHI_i = sum_p ( share of partner p in product i )^2

Ranges from 1/N (perfectly spread over N partners) to 1 (single partner).
Conventional reading (shares in 0-1): < 0.15 diversified, 0.15-0.25 moderate,
> 0.25 concentrated. We also return the top partner and its share, which is
what people actually want to see in a table.
"""

from __future__ import annotations

import pandas as pd

from ..config import AGGREGATE_PARTNERS, FOCUS


def _bilateral(df: pd.DataFrame, reporter: str, flow: str) -> pd.DataFrame:
    return df[(df["reporter"] == reporter) & (df["flow"] == flow) & (~df["partner"].isin(AGGREGATE_PARTNERS))]


def hhi_by_product(df: pd.DataFrame, period: str, flow: str, reporter: str = FOCUS, min_value: float = 0.0) -> pd.DataFrame:
    """One row per product: hhi, top_partner, top_share, total, n_partners."""
    sub = _bilateral(df, reporter, flow)
    sub = sub[sub["period"] == period]
    if sub.empty:
        return pd.DataFrame(columns=["product", "hhi", "top_partner", "top_share", "total", "n_partners"])

    g = sub.groupby(["product", "partner"], as_index=False)["value"].sum()
    g["total"] = g.groupby("product")["value"].transform("sum")
    g = g[g["total"] > min_value]
    g["share"] = g["value"] / g["total"]

    hhi = g.groupby("product")["share"].apply(lambda s: float((s**2).sum())).rename("hhi")
    top = g.sort_values("share", ascending=False).drop_duplicates("product").set_index("product")
    out = pd.DataFrame(
        {
            "hhi": hhi,
            "top_partner": top["partner"],
            "top_share": top["share"],
            "total": top["total"],
            "n_partners": g.groupby("product")["partner"].nunique(),
        }
    )
    return out.sort_values("hhi", ascending=False).rename_axis("product").reset_index()


def hhi_over_time(df: pd.DataFrame, flow: str, reporter: str = FOCUS, products: list[str] | None = None, freq: str = "A") -> pd.DataFrame:
    """Long table: period, product, hhi, top_partner, top_share."""
    periods = sorted(df.loc[df["freq"] == freq, "period"].unique())
    frames = []
    for per in periods:
        h = hhi_by_product(df, per, flow, reporter)
        if products is not None:
            h = h[h["product"].isin(products)]
        frames.append(h.assign(period=per))
    if not frames:
        return pd.DataFrame(columns=["period", "product", "hhi", "top_partner", "top_share"])
    return pd.concat(frames, ignore_index=True)[["period", "product", "hhi", "top_partner", "top_share", "total"]]


def weighted_hhi(hhi_table: pd.DataFrame) -> float:
    """Single number for a country-year: HHI averaged over products, weighted by trade value."""
    if hhi_table.empty or hhi_table["total"].sum() == 0:
        return float("nan")
    return float((hhi_table["hhi"] * hhi_table["total"]).sum() / hhi_table["total"].sum())
