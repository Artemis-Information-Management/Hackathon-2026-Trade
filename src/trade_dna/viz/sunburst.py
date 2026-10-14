"""Sunburst of the pruned product tree (HS2 -> CN8)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .theme import PALETTE, apply_theme


def product_sunburst(nodes: pd.DataFrame, title: str = "Product tree", max_depth: int = 3) -> go.Figure:
    colors = ["#DDE1E6" if o else c for o, c in zip(nodes["is_other"], _level_colors(nodes))]
    fig = go.Figure(
        go.Sunburst(
            ids=nodes["id"],
            labels=nodes["label"],
            parents=nodes["parent"],
            values=nodes["value"],
            branchvalues="total",
            maxdepth=max_depth,
            marker=dict(colors=colors, line=dict(width=1, color="white")),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} EUR<br>%{percentParent:.1%} of parent<extra></extra>",
            insidetextorientation="radial",
        )
    )
    fig.update_layout(title=title)
    return apply_theme(fig, height=620)


def _level_colors(nodes: pd.DataFrame) -> list[str]:
    """Colour by top-level HS2 chapter so a branch keeps one hue as you zoom."""
    chapter_of = {}
    for _, r in nodes.iterrows():
        if r["level"] == 2:
            chapter_of[r["id"]] = r["id"]
    palette = PALETTE["categorical"]
    chapters = sorted(set(chapter_of.values()))
    colour_of_chapter = {c: palette[i % len(palette)] for i, c in enumerate(chapters)}
    out = []
    for _, r in nodes.iterrows():
        if r["level"] == 0:
            out.append("white")
        else:
            chapter = str(r["id"])[:2]
            out.append(colour_of_chapter.get(chapter, PALETTE["muted"]))
    return out
