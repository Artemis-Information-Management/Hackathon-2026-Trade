"""Lens 5 - Luxembourg's partners: the bilateral flows, country by country.

Everything here is declared BY Luxembourg (reporter = LU):

    flow 1  imports  = what Luxembourg buys FROM partner p
    flow 2  exports  = what Luxembourg sells TO partner p

No "World" line is used: the partner must be a real country (aggregates such as
WORLD or EU27_2020 and Eurostat's special codes are dropped), so the shares are
shares of the sum over named countries.

``product="TOTAL"`` means all products. The real extraction carries a TOTAL row
per partner; when it is missing (synthetic sample) the HS2 chapters are summed.
"""

from __future__ import annotations

import pandas as pd

from ..config import EU27, FOCUS, is_country_partner

ALL_PRODUCTS = "TOTAL"


def _bilateral(df: pd.DataFrame, flow: str, reporter: str = FOCUS, freq: str = "A") -> pd.DataFrame:
    keep = (df["reporter"] == reporter) & (df["flow"] == flow) & (df["freq"] == freq) & is_country_partner(df["partner"])
    return df[keep]


def _one_product(sub: pd.DataFrame, product: str) -> pd.DataFrame:
    """Rows for one product; TOTAL falls back to the sum of HS2 chapters when absent."""
    if product != ALL_PRODUCTS:
        return sub[sub["product"] == product]
    tot = sub[sub["product"] == ALL_PRODUCTS]
    if len(tot):
        return tot
    return sub[sub["product"].str.len() == 2]


def partner_table(df: pd.DataFrame, flow: str, period: str, product: str = ALL_PRODUCTS, reporter: str = FOCUS) -> pd.DataFrame:
    """One row per partner country: value (EUR), share (0-1), is_eu. Biggest first."""
    sub = _one_product(_bilateral(df, flow, reporter), product)
    sub = sub[sub["period"] == period]
    g = sub.groupby("partner", as_index=False)["value"].sum()
    g = g[g["value"] > 0]
    total = g["value"].sum()
    g["share"] = g["value"] / total if total > 0 else 0.0
    g["is_eu"] = g["partner"].isin(EU27)
    return g.sort_values(["value", "partner"], ascending=[False, True]).reset_index(drop=True)


def partner_shares_over_time(
    df: pd.DataFrame, flow: str, partners: list[str], product: str = ALL_PRODUCTS, reporter: str = FOCUS
) -> pd.DataFrame:
    """Long table: period, partner, value, share (share of all named countries that year)."""
    sub = _one_product(_bilateral(df, flow, reporter), product)
    g = sub.groupby(["period", "partner"], as_index=False)["value"].sum()
    g["share"] = g["value"] / g.groupby("period")["value"].transform("sum")
    out = g[g["partner"].isin(partners)]
    return out.sort_values(["partner", "period"]).reset_index(drop=True)


def partner_product_mix(df: pd.DataFrame, flow: str, period: str, partner: str, reporter: str = FOCUS, n: int = 10) -> pd.DataFrame:
    """What flows between Luxembourg and ONE partner, by HS2 chapter: product, value, share.

    The ``n`` biggest chapters are listed, the rest folded into "Other chapters (k)".
    """
    sub = _bilateral(df, flow, reporter)
    sub = sub[(sub["partner"] == partner) & (sub["period"] == period) & (sub["product"].str.len() == 2)]
    g = sub.groupby("product", as_index=False)["value"].sum()
    g = g[g["value"] > 0].sort_values("value", ascending=False)
    total = g["value"].sum()
    head, tail = g.head(n), g.iloc[n:]
    if len(tail):
        head = pd.concat([head, pd.DataFrame([{"product": f"Other chapters ({len(tail)})", "value": tail["value"].sum()}])])
    head = head.reset_index(drop=True)
    head["share"] = head["value"] / total if total > 0 else 0.0
    return head
