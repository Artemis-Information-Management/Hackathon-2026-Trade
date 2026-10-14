"""Lens 1 - Trade twins: who does Luxembourg look like?

Finger-Kreinin export similarity index (Finger & Kreinin, 1979):

    FK(a, b) = sum_i min( s_ai , s_bi )

where s_ai is the share of product i in country a's total exports
(or imports). It ranges from 0 (nothing in common) to 1 (identical profile).
It is symmetric, bounded, and economists on the jury will recognise it.
"""

from __future__ import annotations

import pandas as pd

from ..config import FOCUS


def product_shares(df: pd.DataFrame, flow: str, period: str, partner: str = "WORLD") -> pd.DataFrame:
    """Matrix reporter x product of shares (rows sum to 1) for one flow/period."""
    sub = df[(df["flow"] == flow) & (df["period"] == period) & (df["partner"] == partner)]
    mat = sub.pivot_table(index="reporter", columns="product", values="value", aggfunc="sum").fillna(0.0)
    totals = mat.sum(axis=1)
    mat = mat[totals > 0]
    return mat.div(mat.sum(axis=1), axis=0)


def finger_kreinin(shares: pd.DataFrame, focus: str = FOCUS) -> pd.Series:
    """FK similarity of every reporter with ``focus``; the focus itself scores 1."""
    if focus not in shares.index:
        return pd.Series(dtype=float, name="fk")
    ref = shares.loc[focus]
    fk = shares.clip(upper=ref, axis=1).sum(axis=1)
    fk.name = "fk"
    return fk.sort_values(ascending=False)


def similarity_over_time(
    df: pd.DataFrame,
    flow: str,
    focus: str = FOCUS,
    partner: str = "WORLD",
    freq: str = "A",
) -> pd.DataFrame:
    """Long table: period, reporter, fk (similarity with focus in that period)."""
    out = []
    periods = sorted(df.loc[df["freq"] == freq, "period"].unique())
    for per in periods:
        fk = finger_kreinin(product_shares(df, flow, per, partner), focus)
        if len(fk):
            out.append(fk.rename_axis("reporter").reset_index().assign(period=per))
    if not out:
        return pd.DataFrame(columns=["period", "reporter", "fk"])
    return pd.concat(out, ignore_index=True)[["period", "reporter", "fk"]]


def top_twins(sim_long: pd.DataFrame, period: str, n: int = 5, focus: str = FOCUS) -> pd.DataFrame:
    sub = sim_long[(sim_long["period"] == period) & (sim_long["reporter"] != focus)]
    return sub.nlargest(n, "fk").reset_index(drop=True)
