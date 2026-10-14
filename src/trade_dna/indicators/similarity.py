"""Lens 1 - Trade twins: who does Luxembourg look like?

Finger-Kreinin export similarity index (Finger & Kreinin, 1979):

    FK(a, b) = sum_i min( s_ai , s_bi )

where s_ai is the share of product i in country a's total exports
(or imports). It ranges from 0 (nothing in common) to 1 (identical profile).
It is symmetric, bounded, and economists on the jury will recognise it.

The score is a sum over products, so it can be taken apart: the term
min(s_ai, s_bi) is what product i contributes. ``product_overlap`` returns
those terms, which is what the "Look inside the basket" charts show.
"""

from __future__ import annotations

import pandas as pd

from ..config import FOCUS


def product_shares(df: pd.DataFrame, flow: str, period: str, partner: str = "WORLD") -> pd.DataFrame:
    """Matrix reporter x product of shares (rows sum to 1) for one flow/period."""
    sub = df[(df["flow"] == flow) & (df["period"] == period) & (df["partner"] == partner)]
    # HS2 chapters only: the data also holds the TOTAL line (and finer codes),
    # which would be counted as one more "product" and inflate every similarity.
    sub = sub[sub["product"].str.len() == 2]
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


# --------------------------------------------------------------------------
# Product dimension: what is the score made of?
# --------------------------------------------------------------------------
def other_label(n: int) -> str:
    """Label of the row that folds the n smallest chapters together."""
    return f"Other chapters ({n})"


def product_overlap(shares: pd.DataFrame, other: str, focus: str = FOCUS) -> pd.DataFrame:
    """Chapter-by-chapter breakdown of the similarity between ``focus`` and ``other``.

    Returns one row per chapter with three columns (all shares, 0-1):
      focus   share of the chapter in the focus country's trade
      other   share of the chapter in the other country's trade
      common  min(focus, other): the part the two baskets have in common

    ``common.sum()`` is exactly the Finger-Kreinin score, which is the whole point:
    the chart adds up to the number shown on the map.
    """
    out = pd.DataFrame({"focus": shares.loc[focus], "other": shares.loc[other]})
    out["common"] = out[["focus", "other"]].min(axis=1)
    out.index.name = "product"
    return out.sort_values("common", ascending=False)


def collapse_overlap(overlap: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Keep the ``n`` biggest chapters (by focus + other share), fold the rest in one row.

    The folded row sums focus, other and common, so every column total is unchanged
    (common stays the sum of the per-chapter minima, not the minimum of the sums).
    Chapters absent from both countries are dropped.
    """
    live = overlap[(overlap["focus"] > 0) | (overlap["other"] > 0)]
    ranked = live.assign(_w=live["focus"] + live["other"]).sort_values("_w", ascending=False).drop(columns="_w")
    head, tail = ranked.head(n), ranked.iloc[n:]
    if tail.empty:
        return head
    folded = pd.DataFrame([tail.sum()], index=[other_label(len(tail))])
    folded.index.name = "product"
    return pd.concat([head, folded])


def overlap_summary(overlap: pd.DataFrame, k: int = 3) -> dict:
    """Facts for a one-sentence reading of ``overlap`` (uses the full, uncollapsed table).

    top_common    the k chapters that contribute most to the score: [(code, common), ...]
    gap           the chapter where the two baskets differ most:
                  (code, focus share, other share), or None
    """
    ranked = overlap.sort_values("common", ascending=False)
    top = [(code, float(row["common"])) for code, row in ranked.head(k).iterrows() if row["common"] > 0]
    diff = (overlap["focus"] - overlap["other"]).abs()
    gap = None
    if len(diff) and diff.max() > 0:
        code = diff.idxmax()
        gap = (code, float(overlap.loc[code, "focus"]), float(overlap.loc[code, "other"]))
    return {"top_common": top, "gap": gap}


def common_matrix(shares: pd.DataFrame, countries: list[str], focus: str = FOCUS, n: int = 10) -> pd.DataFrame:
    """Chapters x countries table of contributions min(s_focus, s_country), shares 0-1.

    The ``n`` chapters that contribute most (summed over the countries) are listed,
    the others are folded into one row, so each column adds up to that country's
    Finger-Kreinin score.
    """
    countries = [c for c in countries if c in shares.index and c != focus]
    ref = shares.loc[focus]
    m = shares.loc[countries].clip(upper=ref, axis=1).T
    m = m.loc[m.sum(axis=1).sort_values(ascending=False).index]
    m = m[m.sum(axis=1) > 0]
    head, tail = m.head(n), m.iloc[n:]
    if tail.empty:
        return head
    folded = pd.DataFrame([tail.sum()], index=[other_label(len(tail))])
    return pd.concat([head, folded])


def product_twins(shares: pd.DataFrame, product: str, focus: str = FOCUS) -> pd.DataFrame:
    """Who looks most like ``focus`` on ONE chapter? One row per other reporter.

    share        weight of the chapter in that country's trade (0-1)
    focus_share  the same weight for the focus country (constant column)
    gap          |share - focus_share|: how far apart the two countries are on this chapter
    common       min(share, focus_share): what this chapter adds to their similarity score

    Sorted by ``gap`` (closest first). The gap is this chapter's own term in the distance
    behind the score: summed over all chapters it equals 2 x (1 - Finger-Kreinin).
    """
    ref = float(shares.loc[focus, product])
    s = shares[product].drop(focus, errors="ignore")
    out = pd.DataFrame({"share": s})
    out["focus_share"] = ref
    out["gap"] = (out["share"] - ref).abs()
    out["common"] = out["share"].clip(upper=ref)
    out.index.name = "reporter"
    return out.reset_index().sort_values(["gap", "reporter"]).set_index("reporter")
