"""Lens 3 - Smart zoom: HS2 -> HS4 -> HS6 -> CN8 without drowning the reader.

The brief asks how to display increasingly detailed product codes while
highlighting only the most significant flows. Our answer: at every node of
the product tree keep the ``top_k`` children (and anything above
``min_share`` of the parent) and fold the rest into a single "Other" leaf.
The result is a small tree that a sunburst/treemap can show in one glance,
with the long tail still accounted for (it is never silently dropped).
"""

from __future__ import annotations

import pandas as pd

from ..config import hs2_label

LEVELS = (2, 4, 6, 8)


def _level_totals(df: pd.DataFrame, level: int) -> pd.Series:
    codes = df["product"].str[:level]
    return df.groupby(codes)["value"].sum()


def prune_hierarchy(
    df: pd.DataFrame,
    top_k: int = 5,
    min_share: float = 0.02,
    root_label: str = "Total",
    max_level: int = 8,
) -> pd.DataFrame:
    """Return a node table (id, parent, label, value, level, is_other) for a sunburst.

    ``df`` must contain at least ``product`` (codes of a single finest length,
    e.g. all CN8) and ``value``. Codes are truncated to build the upper levels.
    """
    df = df[["product", "value"]].copy()
    df["product"] = df["product"].astype(str)
    finest = int(df["product"].str.len().max())
    levels = [lv for lv in LEVELS if lv <= min(finest, max_level)]
    totals = {lv: _level_totals(df, lv) for lv in levels}

    rows: list[dict] = [
        {"id": "root", "parent": "", "label": root_label, "value": float(df["value"].sum()), "level": 0, "is_other": False}
    ]

    def expand(parent_id: str, parent_code: str, level_idx: int) -> None:
        if level_idx >= len(levels):
            return
        lv = levels[level_idx]
        tot = totals[lv]
        children = tot[tot.index.str.startswith(parent_code)].sort_values(ascending=False)
        if children.empty:
            return
        parent_total = float(children.sum())
        in_top_k = children.rank(ascending=False, method="first") <= top_k
        big_enough = (children / parent_total >= min_share) if min_share > 0 else pd.Series(False, index=children.index)
        keep = children[in_top_k | big_enough]
        rest = children.drop(keep.index)
        for code, val in keep.items():
            node_id = code
            rows.append(
                {
                    "id": node_id,
                    "parent": parent_id,
                    "label": hs2_label(code) if lv == 2 else code,
                    "value": float(val),
                    "level": lv,
                    "is_other": False,
                }
            )
            expand(node_id, code, level_idx + 1)
        if len(rest):
            rows.append(
                {
                    "id": f"{parent_id}_other",
                    "parent": parent_id,
                    "label": f"Other ({len(rest)})",
                    "value": float(rest.sum()),
                    "level": lv,
                    "is_other": True,
                }
            )

    expand("root", "", 0)
    return pd.DataFrame(rows)
